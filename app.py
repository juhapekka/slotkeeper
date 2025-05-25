from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from Database import Database

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
        return render_template('index.html', username=session['username'], devices=devices, query=query)
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

if __name__ == '__main__':
    app.run(debug=True)

