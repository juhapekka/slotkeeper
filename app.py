from datetime import datetime
from functools import wraps
import time
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import config
from Database import Database
import slotkeeperutil as su

app = Flask(__name__)
ITEMS_PER_PAGE = 20

def login_required_with_csrf(f):
    '''wrapper to check login and for POST csrf status'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return render_template('login.html',
                                   error='Session error.',
                                   csrf_token=session['csrf_token'])
        if request.method == 'POST' and not su.check_csrf_token(session, request.form):
            return render_template('login.html',
                                   error='Session error.',
                                   csrf_token=session['csrf_token'])
        return f(*args, **kwargs)
    return decorated_function

def fill_in_device_list(devices):
    '''build device list for ui'''
    device_data = []
    user = db.get_user_by_username(session['username'])

    for device in devices:
        reservation = db.get_active_reservation_for_device(device['id'])
        owned = reservation and reservation['user_id'] == user['id'] if reservation else False
        desc = device['description'] or ''

        # cut excessive long description to preview
        lines = desc.splitlines()
        preview = '\n'.join(lines[:3])[:250]
        if len(desc) > 250 or desc.count('\n') >= 3:
            preview += '\n...'

        device_data.append(
            {
                'device': device,
                'reservation': reservation,
                'user_owned': owned,
                'preview': preview
            }
        )
    return device_data

app.secret_key = config.secret_key  # Used to sign session cookies

DATABASE = 'database.db'

'''Instantiate the Database class'''
db = Database(DATABASE)

@app.route('/')
def index():
    '''Base index.html rendering'''
    if 'username' in session:
        user = db.get_user_by_username(session['username'])
        user_id = user['id'] if user else None

        query = request.args.get('q', '')
        only_mine = request.args.get('only_mine') == '1'

        try:
            page = int(request.args.get('page', 1))
        except ValueError:
            page = 1
        page = max(page, 1)

        devices = db.search_devices(query, user_id, only_mine, page=page, limit=ITEMS_PER_PAGE)
        device_data = fill_in_device_list(devices['items'])

        csrf_token = su.generate_csrf_token(session)
        return render_template(
            'index.html',
            username=session['username'],
            devices=device_data,
            query=query,
            only_mine=only_mine,
            csrf_token=csrf_token,
            current_page=page,
            total_pages=int(devices['total'] / ITEMS_PER_PAGE))
    return render_template('index.html', username=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    '''Handle registration'''
    error = None
    if request.method == 'POST':
        if not su.check_csrf_token(session, request.form):
            return render_template('login.html',
                                   error='Invalid CSRF token.',
                                   csrf_token=session['csrf_token'])

        username = request.form['username'].strip()
        password = request.form['password'].strip()
        password_hash = generate_password_hash(password)

        if not username or not password:
            error = 'Username and password are required.'
        elif len(username) > 32:
            error = 'Username too long (max 32 characters).'
        elif len(password) < 6:
            error = 'Password too short (min 6 characters).'

        if not error:
            if db.create_user(username, password_hash):
                return redirect(url_for('login'))
            else:
                error='Username already exists.'
    else:
        su.generate_csrf_token(session)

    return render_template('register.html',
                            error=error,
                            csrf_token=session['csrf_token'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''Handle login'''
    if request.method == 'POST':
        if not su.check_csrf_token(session, request.form):
            return render_template('login.html',
                                   error='Invalid CSRF token.',
                                   csrf_token=session['csrf_token'])

        username = request.form['username']
        password = request.form['password']

        user = db.get_user_by_username(username)

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            return redirect(url_for('index'))

        return render_template('login.html',
                                error='Invalid username or password.',
                                csrf_token=session['csrf_token'])

    csrf_token = su.generate_csrf_token(session)
    return render_template('login.html', csrf_token=csrf_token)

@app.route('/logout')
def logout():
    '''Log out..'''
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/add_device', methods=['GET', 'POST'])
@login_required_with_csrf
def add_device():
    '''Handle adding new device from UI'''
    if request.method == 'POST':
        name = request.form['name'].strip()
        description = request.form['description']
        user = db.get_user_by_username(session['username'])

        if not name:
            return render_template('add_device.html',
                                   error='Device name is required.',
                                   csrf_token=session['csrf_token'])

        if len(name) > 32:
            return render_template('add_device.html',
                                   error='Device name too long (max 32 characters).',
                                   csrf_token=session['csrf_token'])

        if len(description) > 4096:
            return render_template('add_device.html',
                                   error='Description too long (max 4096 characters).',
                                   csrf_token=session['csrf_token'])

        if user:
            db.add_device(name, description, user['id'])
            return redirect(url_for('index'))

        return redirect(url_for('login'))

    csrf_token = su.generate_csrf_token(session)
    return render_template('add_device.html', csrf_token=csrf_token)

@app.route('/edit_device/<int:device_id>', methods=['GET', 'POST'])
@login_required_with_csrf
def edit_device(device_id):
    '''Handle editing device from UI'''
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        db.update_device(device_id, name, description)
        return redirect(url_for('index'))

    device = db.get_device_by_id(device_id)
    if device:
        csrf_token = su.generate_csrf_token(session)
        return render_template('edit_device.html', device=device, csrf_token=csrf_token)

    return redirect(url_for('index'))

@app.route('/delete_device/<int:device_id>', methods=['POST'])
@login_required_with_csrf
def delete_device(device_id):
    '''Handle deleting device from UI'''
    db.delete_device(device_id)
    return redirect(url_for('index'))

@app.route('/reserve/<int:device_id>', methods=['GET', 'POST'])
def reserve(device_id):
    '''Handle reserve device from UI'''
    user = db.get_user_by_username(session['username'])
    if not user:
        return 'Error: User not found.'
    user_id = user['id'] if user else None

    if request.method == 'POST':
        reserved_until = request.form['reserved_until']
        original_page = request.form.get('original_page', 1, type=int)
        original_query = request.form.get('original_query', '')
        original_only_mine_str = request.form.get('original_only_mine', '')
        original_only_mine_bool = original_only_mine_str == '1'

        try:
            reserved_int = int(datetime.strptime(reserved_until, '%Y-%m-%dT%H:%M').timestamp())
            if reserved_int <= time.time():
                return render_template(
                    'index.html',
                    username=session['username'],
                    modal_error='Reservation must be in the future.',
                    csrf_token=session['csrf_token']
                )
        except ValueError:
            return render_template(
                'index.html',
                username=session['username'],
                modal_error='Invalid reservation time format.',
                csrf_token=session['csrf_token']
            )

        success = db.create_reservation(user['id'], device_id, reserved_until)
        if success:
            return redirect(url_for('index',
                                    page=original_page,
                                    q=original_query,
                                    only_mine=('1' if original_only_mine_bool else None)))


        return redirect(url_for('reserve', device_id=device_id))

    device = db.get_device_by_id(device_id)
    if device:
        query = request.args.get('q', '')
        only_mine = request.args.get('only_mine') == '1'

        try:
            page = int(request.args.get('page', 1))
        except ValueError:
            page = 1
        page = max(page, 1)

        devices = db.search_devices(query, user_id, only_mine, page=page, limit=ITEMS_PER_PAGE)
        device_data = fill_in_device_list(devices['items'])

        csrf_token = su.generate_csrf_token(session)
        return render_template(
            'index.html',
            username=session['username'],
            devices=device_data,
            query=query,
            only_mine=only_mine,
            show_reservation_modal=True,
            modal_device=device,
            modal_error=None,
            csrf_token=csrf_token,
            current_page=page,
            total_pages=int(devices['total'] / ITEMS_PER_PAGE))
    return render_template(
            'index.html',
            username=session['username'],
            modal_error='Device not Found!',
            csrf_token=session['csrf_token']
        )

@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
@login_required_with_csrf
def cancel_reservation(reservation_id):
    '''Handle releasing reservation from UI'''
    user = db.get_user_by_username(session['username'])
    db.cancel_reservation(reservation_id, user['id'])
    original_page = request.form.get('original_page', 1, type=int)
    original_query = request.form.get('original_query', '')
    original_only_mine_str = request.form.get('original_only_mine', '')
    original_only_mine_bool = original_only_mine_str == '1'

    return redirect(url_for('index',
                            page=original_page,
                            q=original_query,
                            only_mine=('1' if original_only_mine_bool else None)))

@app.template_filter('datetimeformat')
def datetimeformat(value):
    '''Simple datetime formatter'''
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M')

@app.route('/device/<int:device_id>')
@login_required_with_csrf
def view_device(device_id):
    '''Detail view of device'''
    user = db.get_user_by_username(session['username'])
    if not user:
        return redirect(url_for('login'))
    user_id = user['id']

    modal_device = db.get_device_by_id(device_id)
    if not modal_device:
        return render_template(
            'index.html',
            username=session['username'],
            modal_error='Device not Found!',
            csrf_token=session['csrf_token']
        )

    comments = db.get_comments_for_device(device_id)

    query = request.args.get('q', '')
    only_mine = request.args.get('only_mine') == '1'

    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    page = max(page, 1)

    devices = db.search_devices(query, user_id, only_mine, page=page, limit=ITEMS_PER_PAGE)

    device_data = fill_in_device_list(devices['items'])

    error_message = request.args.get('error')
    csrf_token = su.generate_csrf_token(session)

    return render_template(
        'index.html',
        username=session['username'],
        devices=device_data,
        query=query,
        only_mine=only_mine,
        modal_device=modal_device,
        comments=comments,
        current_user_id=user['id'],
        show_device_detail_modal=True,
        modal_error=error_message,
        csrf_token=csrf_token,
        current_page=page,
        total_pages=int(devices['total'] / ITEMS_PER_PAGE))

def generate_pie_chart_segments(device_list, colors, value_key='value', label_key='name',
                                preform_key=None):
    '''generate data to be shown in pie chart. top 3 machines + rest.'''
    pie_data = []
    gradient_parts = []
    total_value = sum(item.get(value_key, 0) for item in device_list)
    cur_angle = 0

    if total_value > 0:
        sorted_data = sorted(device_list, key=lambda x: x.get(value_key, 0), reverse=True)
        top_n = 3
        num_items_total = len(sorted_data)

        pie_items = []
        if num_items_total <= top_n:
            pie_items.extend(sorted_data)
        else:
            pie_items.extend(sorted_data[:top_n])
            others_value = sum(d.get(value_key, 0) for d in sorted_data[top_n:])
            if others_value > 0:
                other_item_data = {label_key: 'Other Devices', value_key: others_value}
                if preform_key == 'formatted_duration':
                    other_item_data[preform_key] = su.format_duration_to_string(others_value)
                pie_items.append(other_item_data)

        for i, input_list in enumerate(pie_items):
            item_nvalue = input_list.get(value_key, 0)
            percentage = 0
            if total_value > 0:
                percentage = (item_nvalue / total_value) * 100

            # dict to template
            item_dict = {
                'name': input_list.get(label_key, 'Unknown'),
                'value_numeric': item_nvalue,
                'percentage': round(percentage, 1),
                'color': colors[i % len(colors)]
            }

            if preform_key:
                if preform_key in input_list:
                    item_dict[preform_key] = input_list[preform_key]
                else:
                    item_dict[preform_key] = str(item_nvalue)

            pie_data.append(item_dict)

            start_percentage = cur_angle
            is_last_segment = i == len(pie_items) - 1
            if is_last_segment and cur_angle < 100:
                cur_angle = 100.0
            elif total_value > 0 :
                cur_angle += percentage
            cur_angle = min(max(cur_angle, 0), 100.0)
            start_percentage = min(max(start_percentage,0), 100.0)
            gradient_parts.append(
                f'{colors[i % len(colors)]} {round(start_percentage, 2)}% {round(cur_angle, 2)}%'
            )

    conic_gradient_style = ''
    if gradient_parts:
        conic_gradient_style = f'background: conic-gradient({', '.join(gradient_parts)});'
    return pie_data, conic_gradient_style, (total_value > 0)

@app.route('/user')
@login_required_with_csrf
def user_page():
    '''Show user page on UI'''
    username = session['username']
    reservations = db.get_active_reservations_by_user(username)
    devices = db.get_devices_created_by_user(username)
    last_reservations = db.get_last_reservations_by_user(username)
    user = db.get_user_by_username(username)

    if not user:
        session.pop('username', None)
        session.pop('user_id', None)
        return redirect(url_for('login', error='User data not found, please log in again.'))

    user_id = user['id']

    device_res_counts = db.get_user_device_reservation_counts(user_id)
    pie_colors_counts = ['#F15854', '#5DA5DA', '#DECF3F', '#4D4D4D']

    pie_data_counts, gradient_counts, has_pie_counts = generate_pie_chart_segments(
        device_res_counts,
        pie_colors_counts,
        label_key='device_name',
        value_key='reservation_count')

    device_res_durations = db.get_user_device_reservation_durations(user_id)

    processed_device_res_durations = []
    for item in device_res_durations:
        processed_device_res_durations.append({
            'device_name': item.get('device_name', 'Unknown Device'),
            'total_duration_seconds': item.get('total_duration_seconds', 0),
            'formatted_duration': su.format_duration_to_string(item.get('total_duration_seconds', 0))
        })

    pie_data_durations, gradient_durations, has_pie_durations = generate_pie_chart_segments(
        processed_device_res_durations,
        pie_colors_counts,
        value_key='total_duration_seconds',
        label_key='device_name',
        preform_key='formatted_duration')

    return render_template('user_page.html',
                           username=username,
                           reservations=reservations,
                           devices=devices,
                           last_reservations=last_reservations,
                           pie_chart_data_counts=pie_data_counts,
                           conic_gradient_style_counts=gradient_counts,
                           has_reservations_for_pie_counts=has_pie_counts,
                           pie_chart_data_durations=pie_data_durations,
                           conic_gradient_style_durations=gradient_durations,
                           has_reservations_for_pie_durations=has_pie_durations)

@app.route('/device/<int:device_id>/add_comment', methods=['POST'])
@login_required_with_csrf
def add_comment_to_device(device_id):
    '''Add comment to device, on device page'''
    user = db.get_user_by_username(session['username'])
    if not user:
        return 'User not found', 403

    content = request.form.get('comment_content')
    if not content or len(content.strip()) == 0:
        return redirect(url_for('view_device',
                                device_id=device_id,
                                error='Comment cannot be empty.'))

    if len(content) > 1024:
        return redirect(url_for('view_device',
                                device_id=device_id,
                                error='Comment too long (max 1024 chars).'))

    original_page = request.form.get('original_page', 1, type=int)
    original_query = request.form.get('original_query', '')
    original_only_mine_str = request.form.get('original_only_mine', '')
    original_only_mine_bool = original_only_mine_str == '1'

    if db.add_comment(device_id, user['id'], content.strip()):
        return redirect(url_for('view_device',
                                device_id=device_id,
                                page=original_page,
                                q=original_query,
                                only_mine=('1' if original_only_mine_bool else None)))
    else:
        return redirect(url_for('view_device',
                                device_id=device_id,
                                error='Failed to add comment.',
                                page=original_page,
                                q=original_query,
                                only_mine=('1' if original_only_mine_bool else None)))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required_with_csrf
def delete_comment_route(comment_id):
    '''Remove comment from device, on device page'''
    user = db.get_user_by_username(session['username'])
    if not user:
        return 'User not found', 403

    comment_to_delete = db.get_comment_by_id(comment_id)
    if not comment_to_delete:
        return redirect(url_for('index'))

    device_id_for_redirect = comment_to_delete['device_id']

    if db.delete_comment(comment_id, user['id']):
        return redirect(url_for('view_device',
                                device_id=device_id_for_redirect))

    return redirect(url_for('view_device',
                            device_id=device_id_for_redirect,
                            error='Could not delete comment or not authorized.'))

if __name__ == '__main__':
    app.run(debug=True)
