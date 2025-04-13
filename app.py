from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'super-secret-key'  # 本番ではもっとランダムにしてね！

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('index.html', error=None)

@app.route('/greet', methods=['POST'])
def greet():
    username = request.form['username']
    return render_template('greet.html', name=username)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/list')
def show_list():
    names = ['さくら', 'たろう', 'じろう']  # ← ここは動的にすることもできる
    return render_template('list.html', names=names)

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['username'].strip()

    if 'username' not in session:
        return redirect('/login')

    if not name:
        return render_template('index.html', error='名前を入力してください')
    if len(name) > 20:
        return render_template('index.html', error='名前は20文字以内で入力してください')

    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 重複チェック
    c.execute('SELECT * FROM users WHERE name = ? AND user_id = (SELECT id FROM login_users WHERE username = ?)', (name, session['username']))
    if c.fetchone():
        conn.close()
        return render_template('index.html', error='その名前はすでに登録されています')

    # ログインユーザーの ID を取得
    c.execute('SELECT id FROM login_users WHERE username = ?', (session['username'],))
    user_row = c.fetchone()
    if not user_row:
        conn.close()
        return redirect('/login')
    user_id = user_row['id']

    # 画像処理
    image = request.files.get('image')
    image_filename = None

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_filename = f"{name}_{filename}"
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

    # 登録（画像あり）
    c.execute('INSERT INTO users (name, user_id, image_filename) VALUES (?, ?, ?)', (name, user_id, image_filename))
    conn.commit()
    conn.close()

    return redirect('/names')

@app.route('/names')
def show_names():
    if 'username' not in session:
        return redirect('/login')

    keyword = request.args.get('q', '')

    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT id FROM login_users WHERE username = ?', (session['username'],))
    user_id = c.fetchone()['id']

    if keyword:
        c.execute('SELECT * FROM users WHERE user_id = ? AND name LIKE ?', (user_id, '%' + keyword + '%'))
    else:
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))

    users = c.fetchall()
    conn.close()
    return render_template('list.html', users=users, keyword=keyword)

@app.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect('/names')

@app.route('/edit/<int:user_id>', methods=['GET'])
def edit_user(user_id):
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return render_template('edit.html', user=user)

@app.route('/update/<int:user_id>', methods=['POST'])
def update_user(user_id):
    new_name = request.form['username']
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('UPDATE users SET name = ? WHERE id = ?', (new_name, user_id))
    conn.commit()
    conn.close()
    return redirect('/names')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            return render_template('register.html', error='両方入力してください')

        hashed_pw = generate_password_hash(password)

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

@app.route('/login', methods=['GET', 'POST'])
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
            return redirect('/dashboard')  # ログイン成功後のページ
        else:
            return render_template('login.html', error='ユーザー名またはパスワードが違います')

    return render_template('login.html', error=None)

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
