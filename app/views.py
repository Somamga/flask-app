from flask import Blueprint, render_template, request, redirect, session, url_for, make_response
import sqlite3
import os
from werkzeug.utils import secure_filename
from functools import wraps
import csv

views_bp = Blueprint('views', __name__)

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return func(*args, **kwargs)
    return wrapper

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@views_bp.route('/')
@login_required
def home():
    return render_template('index.html', error=None)

@views_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    name = request.form['username'].strip()

    # 空欄チェック
    if not name:
        return render_template('index.html', error='名前を入力してください')

    # 文字数制限
    if len(name) > 20:
        return render_template('index.html', error='名前は20文字以内で入力してください')

    # 禁止文字チェック（例：<> /）
    if any(c in name for c in "<>/"):
        return render_template('index.html', error='使用できない文字が含まれています')

    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ログイン中ユーザーのIDを取得
    c.execute('SELECT id FROM login_users WHERE username = ?', (session['username'],))
    user_row = c.fetchone()
    if not user_row:
        conn.close()
        return redirect('/login')
    user_id = user_row['id']

    # 重複チェック（同一ユーザー内）
    c.execute('SELECT * FROM users WHERE name = ? AND user_id = ?', (name, user_id))
    if c.fetchone():
        conn.close()
        return render_template('index.html', error='その名前はすでに登録されています')

    # 画像処理
    image = request.files.get('image')
    image_filename = None

    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        image_filename = f"{name}_{filename}"
        image.save(os.path.join('static/uploads', image_filename))

    # 登録処理
    c.execute('INSERT INTO users (name, user_id, image_filename) VALUES (?, ?, ?)', (name, user_id, image_filename))
    conn.commit()
    conn.close()

    return redirect('/names')

@views_bp.route('/names')
@login_required
def show_names():
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

@views_bp.route('/edit/<int:user_id>')
@login_required
def edit_user(user_id):    
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return render_template('edit.html', user=user)

@views_bp.route('/update/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    new_name = request.form['username']
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('UPDATE users SET name = ? WHERE id = ?', (new_name, user_id))
    conn.commit()
    conn.close()
    return redirect('/names')

@views_bp.route('/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return redirect('/names')

@views_bp.route('/dashboard')
@login_required
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html')
    else:
        return redirect('/login')

@views_bp.route('/export')
@login_required
def export_csv():
    import io
    import csv
    from flask import make_response

    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT id FROM login_users WHERE username = ?', (session['username'],))
    user_id = c.fetchone()['id']
    c.execute('SELECT name, image_filename, created_at FROM users WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()

    # CSVをメモリ上で作成（UTF-8 with BOM対応）
    si = io.StringIO()
    si.write('\ufeff')  # ← これがBOM！
    writer = csv.writer(si)
    writer.writerow(['名前', '画像ファイル名', '登録日時'])  # ヘッダー
    for row in rows:
        writer.writerow([row['name'], row['image_filename'] or '', row['created_at'] or ''])

    output = make_response(si.getvalue())
    output.headers['Content-Disposition'] = 'attachment; filename=export.csv'
    output.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return output
