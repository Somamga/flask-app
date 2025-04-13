from flask import Blueprint, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

def login_required():
    if 'username' not in session:
        return redirect('/login')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            return render_template('register.html', error='両方入力してください')

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')

        try:
            conn = sqlite3.connect('data.db')
            c = conn.cursor()
            c.execute('INSERT INTO login_users (username, password) VALUES (?, ?)', (username, hashed_pw))
            conn.commit()
            conn.close()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return render_template('register.html', error='そのユーザー名は既に使われています')

    return render_template('register.html', error=None)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('data.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM login_users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='ユーザー名またはパスワードが違います')

    return render_template('login.html', error=None)


@auth_bp.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')
