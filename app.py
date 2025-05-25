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
        devices = db.get_all_devices()
        return render_template('index.html', username=session['username'], devices=devices)
    else:
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

if __name__ == '__main__':
    app.run(debug=True)

