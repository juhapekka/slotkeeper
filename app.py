from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from Database import Database
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'super_secret_key'  # Used to sign session cookies

DATABASE = 'database.db'

# Instantiate the Database class
db = Database(DATABASE)

@app.route('/')
def index():
    if 'username' in session:
        query = request.args.get('q', '')
        if query:
            devices = db.search_devices(query)
        else:
            devices = db.get_all_devices()
        user = db.get_user_by_username(session['username'])

        device_data = []
        for device in devices:
            reservation = db.get_active_reservation_for_device(device['id'])
            user_owned = reservation and reservation['user_id'] == user['id'] if reservation else False
            device_data.append({'device': device, 'reservation': reservation, 'user_owned': user_owned})
        
        return render_template('index.html', username=session['username'], devices=device_data, query=query)
    return render_template('index.html', username=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle registration"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        if db.create_user(username, password_hash):
            return redirect(url_for('login'))
        else:
            return "Username already exists."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db.get_user_by_username(username)

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "Invalid username or password."
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Log out.."""
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/add_device', methods=['GET', 'POST'])
def add_device():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        user = db.get_user_by_username(session['username'])

        if user:
            db.add_device(name, description, user['id'])
            return redirect(url_for('index'))
        else:
            return "Error: Logged-in user not found."

    return render_template('add_device.html')

@app.route('/edit_device/<int:device_id>', methods=['GET', 'POST'])
def edit_device(device_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        db.update_device(device_id, name, description)
        return redirect(url_for('index'))

    device = db.get_device_by_id(device_id)
    if device:
        return render_template('edit_device.html', device=device)
    else:
        return "Device not found."

@app.route('/delete_device/<int:device_id>', methods=['POST'])
def delete_device(device_id):
    if 'username' in session:
        db.delete_device(device_id)
    return redirect(url_for('index'))

@app.route('/reserve/<int:device_id>', methods=['GET', 'POST'])
def reserve(device_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    user = db.get_user_by_username(session['username'])
    if not user:
        return "Error: User not found."

    if request.method == 'POST':
        reserved_from = request.form['reserved_from']
        reserved_until = request.form['reserved_until']

        try:
            start_dt = datetime.fromisoformat(reserved_from)
            end_dt = datetime.fromisoformat(reserved_until)
        except ValueError:
            return "Invalid datetime format."

        if end_dt <= start_dt:
            return "Reservation end must be after start."

        success = db.create_reservation(user['id'], device_id, reserved_from, reserved_until)
        if success:
            return redirect(url_for('index'))
        else:
            return "Reservation failed."

    device = db.get_device_by_id(device_id)
    if device:
        return render_template('reserve.html', device=device)
    return "Device not found."

@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    user = db.get_user_by_username(session['username'])
    db.cancel_reservation(reservation_id, user['id'])
    return redirect(url_for('index'))

@app.template_filter('datetimeformat')
def datetimeformat(value):
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M')

if __name__ == '__main__':
    app.run(debug=True)

