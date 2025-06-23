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
DATABASE = 'database.db'
app.secret_key = config.secret_key  # Used to sign session cookies
'''Instantiate the Database class'''
db = Database(DATABASE)

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
        device_data = su.fill_in_device_list(session, db, devices['items'])

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
    user_id = db.get_user_by_username(session['username'])['id']

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

        db.create_reservation(user_id, device_id, reserved_until)
        return redirect(url_for('index',
                                page=original_page,
                                q=original_query,
                                only_mine=('1' if original_only_mine_bool else None)))

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
        device_data = su.fill_in_device_list(session, db, devices['items'])

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
    device_data = su.fill_in_device_list(session, db, devices['items'])

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

@app.route('/user')
@login_required_with_csrf
def user_page():
    '''Show user page on UI'''
    username = session['username']
    reservations = db.get_active_reservations_by_user(username)
    devices = db.get_devices_created_by_user(username)
    user = db.get_user_by_username(username)

    if not user:
        session.pop('username', None)
        session.pop('user_id', None)
        return redirect(url_for('login', error='User data not found, please log in again.'))

    user_id = user['id']

    device_res_counts = db.get_user_device_reservation_counts(user_id)

    pie_data_counts, gradient_counts, has_pie_counts = su.generate_pie_chart_segments(
        device_res_counts,
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

    pie_data_durations, gradient_durations, has_pie_durations = su.generate_pie_chart_segments(
        processed_device_res_durations,
        value_key='total_duration_seconds',
        label_key='device_name',
        preform_key='formatted_duration')

    return render_template('user_page.html',
                           username=username,
                           reservations=reservations,
                           devices=devices,
                           last_reservations=db.get_last_reservations_by_user(username),
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
