from datetime import datetime
from functools import wraps
import time
import uuid
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from Database import Database
import config

app = Flask(__name__)

def generate_csrf_token():
    '''UUID for csrf token'''
    token = str(uuid.uuid4())
    session['csrf_token'] = token
    return token

def check_csrf_token(form):
    '''Check csrf token'''
    token = form.get('csrf_token')
    return token and token == session.get('csrf_token')

def login_required_with_csrf(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return render_template('login.html',
                                   error='Session error.',
                                   csrf_token=session['csrf_token'])
        if request.method == 'POST' and not check_csrf_token(request.form):
            return render_template('login.html',
                                   error='Session error.',
                                   csrf_token=session['csrf_token'])
        return f(*args, **kwargs)
    return decorated_function

app.secret_key = config.secret_key  # Used to sign session cookies

DATABASE = 'database.db'

'''Instantiate the Database class'''
db = Database(DATABASE)

@app.route('/')
def index():
    '''Base index.html rendering'''
    if 'username' in session:
        query = request.args.get('q', '')
        if query:
            devices = db.search_devices(query)
        else:
            devices = db.get_all_devices()
        user = db.get_user_by_username(session['username'])

        query = request.args.get('q', '')
        only_mine = request.args.get('only_mine') == '1'

        device_data = []
        for device in devices:
            reservation = db.get_active_reservation_for_device(device['id'])
            owned = reservation and reservation['user_id'] == user['id'] if reservation else False
            desc = device['description'] or ''

            # cut excessive long description to preview
            lines = desc.splitlines()
            preview = '\n'.join(lines[:3])[:250]
            if len(desc) > 250 or desc.count('\n') >= 3:
                preview += '\n...'

            if only_mine and not owned:
                continue # Only show my own reservations

            device_data.append(
                {
                    'device': device,
                    'reservation': reservation,
                    'user_owned': owned,
                    'preview': preview
                }
            )
        csrf_token = generate_csrf_token()
        return render_template(
            'index.html',
            username=session['username'],
            devices=device_data,
            query=query,
            only_mine=only_mine,
            csrf_token=csrf_token)
    return render_template('index.html', username=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    '''Handle registration'''
    if request.method == 'POST':
        if not check_csrf_token(request.form):
            return render_template('login.html',
                                   error='Invalid CSRF token.',
                                   csrf_token=session['csrf_token'])

        username = request.form['username'].strip()
        password = request.form['password'].strip()
        password_hash = generate_password_hash(password)

        if not username or not password:
            return render_template('register.html',
                                   error='Username and password are required.',
                                   csrf_token=session['csrf_token'])

        if len(username) > 32:
            return render_template('register.html',
                                   error='Username too long (max 32 characters).',
                                   csrf_token=session['csrf_token'])

        if len(password) < 6:
            return render_template('register.html',
                                   error='Password too short (min 6 characters).',
                                   csrf_token=session['csrf_token'])

        if db.create_user(username, password_hash):
            return redirect(url_for('login'))

        return render_template('register.html',
                                error='Username already exists.',
                                csrf_token=session['csrf_token'])
    csrf_token = generate_csrf_token()
    return render_template('register.html', csrf_token=csrf_token)

@app.route('/login', methods=['GET', 'POST'])
def login():
    '''Handle login'''
    if request.method == 'POST':
        if not check_csrf_token(request.form):
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

    csrf_token = generate_csrf_token()
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

    csrf_token = generate_csrf_token()
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
        csrf_token = generate_csrf_token()
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

    if request.method == 'POST':
        reserved_until = request.form['reserved_until']

        try:
            reserved_int = int(datetime.strptime(reserved_until, '%Y-%m-%dT%H:%M').timestamp())
            if reserved_int <= time.time():
                return render_template(
                    'index.html',
                    username=session['username'],
                    modal_error="Reservation must be in the future.",
                    csrf_token=session['csrf_token']
                )
        except Exception:
            return render_template(
                'index.html',
                username=session['username'],
                modal_error="Invalid reservation time format.",
                csrf_token=session['csrf_token']
            )

        success = db.create_reservation(user['id'], device_id, reserved_until)
        if success:
            return redirect(url_for('index'))

        return redirect(url_for('reserve', device_id=device_id))

    device = db.get_device_by_id(device_id)
    if device:
        query = request.args.get('q', '')
        only_mine = request.args.get('only_mine') == '1'
        devices = db.search_devices(query) if query else db.get_all_devices()

        device_data = []
        for d in devices:
            reservation = db.get_active_reservation_for_device(d['id'])
            owned = reservation and reservation['user_id'] == user['id'] if reservation else False
            if only_mine and not owned:
                continue
            device_data.append({'device': d, 'reservation': reservation, 'user_owned': owned})

        csrf_token = generate_csrf_token()
        return render_template(
            'index.html',
            username=session['username'],
            devices=device_data,
            query=query,
            only_mine=only_mine,
            show_reservation_modal=True,
            modal_device=device,
            modal_error=None,
            csrf_token=csrf_token
        )
    return render_template(
            'index.html',
            username=session['username'],
            modal_error="Device not Found!",
            csrf_token=session['csrf_token']
        )

@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
@login_required_with_csrf
def cancel_reservation(reservation_id):
    '''Handle releasing reservation from UI'''
    user = db.get_user_by_username(session['username'])
    db.cancel_reservation(reservation_id, user['id'])
    return redirect(url_for('index'))

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

    modal_device = db.get_device_by_id(device_id)
    if not modal_device:
        return render_template(
            'index.html',
            username=session['username'],
            modal_error="Device not Found!",
            csrf_token=session['csrf_token']
        )

    comments = db.get_comments_for_device(device_id)

    query = request.args.get('q', '')
    only_mine = request.args.get('only_mine') == '1'
    devices = db.search_devices(query) if query else db.get_all_devices()

    device_data = []
    for d in devices:
        reservation = db.get_active_reservation_for_device(d['id'])
        user_owned = reservation and reservation['user_id'] == user['id'] if reservation else False
        if only_mine and not user_owned:
            continue
        device_data.append({'device': d, 'reservation': reservation, 'user_owned': user_owned})

    error_message = request.args.get('error')
    csrf_token = generate_csrf_token()

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
        csrf_token=csrf_token
    )

@app.route('/user')
@login_required_with_csrf
def user_page():
    '''Show user page on UI'''
    username = session['username']
    reservations = db.get_active_reservations_by_user(username)
    devices = db.get_devices_created_by_user(username)
    last_reservations = db.get_last_reservations_by_user(username)
    return render_template('user_page.html',
                           username=username,
                           reservations=reservations,
                           devices=devices,
                           last_reservations=last_reservations)

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

    if db.add_comment(device_id, user['id'], content.strip()):
        return redirect(url_for('view_device',
                                device_id=device_id))
    else:
        return redirect(url_for('view_device',
                                device_id=device_id,
                                error='Failed to add comment.'))

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
