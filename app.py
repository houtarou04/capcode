from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'capcode_secret_key_123' # غيره قبل الرفع

# بيانات الادمن
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '123456'

# مسار رفع الصور
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    conn = sqlite3.connect('portfolio.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, level INTEGER NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        short_desc TEXT,
        full_desc TEXT,
        skills_used TEXT,
        github_link TEXT,
        live_link TEXT,
        img_desktop TEXT,
        img_mobile TEXT,
        price REAL DEFAULT 0
    )''')
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

@app.route('/')
def home():
    conn = get_db()
    skills = conn.execute('SELECT * FROM skills ORDER BY level DESC').fetchall()
    projects = conn.execute('SELECT * FROM projects ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', skills=skills, projects=projects)

@app.route('/project/<int:id>')
def project_detail(id):
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id =?', (id,)).fetchone()
    conn.close()
    if project is None:
        return "المشروع غير موجود", 404
    return render_template('project.html', project=project)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غلط'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    conn = get_db()
    skills = conn.execute('SELECT * FROM skills ORDER BY id DESC').fetchall()
    projects = conn.execute('SELECT * FROM projects ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', skills=skills, projects=projects)

@app.route('/add-skill', methods=['POST'])
@login_required
def add_skill():
    conn = get_db()
    conn.execute('INSERT INTO skills (name, level) VALUES (?,?)', (request.form['name'], request.form['level']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/edit-skill/<int:id>')
@login_required
def edit_skill(id):
    conn = get_db()
    skill = conn.execute('SELECT * FROM skills WHERE id =?', (id,)).fetchone()
    conn.close()
    return render_template('edit-skill.html', skill=skill)

@app.route('/edit-skill/<int:id>', methods=['POST'])
@login_required
def update_skill(id):
    conn = get_db()
    conn.execute('UPDATE skills SET name=?, level=? WHERE id=?', (request.form['name'], request.form['level'], id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/delete-skill/<int:id>')
@login_required
def delete_skill(id):
    conn = get_db()
    conn.execute('DELETE FROM skills WHERE id =?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/add-project', methods=['POST'])
@login_required
def add_project():
    img_d_name, img_m_name = '', ''
    img_d_file = request.files.get('img_d')
    if img_d_file and allowed_file(img_d_file.filename):
        img_d_name = secure_filename(img_d_file.filename)
        img_d_file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_d_name))
    img_m_file = request.files.get('img_m')
    if img_m_file and allowed_file(img_m_file.filename):
        img_m_name = secure_filename(img_m_file.filename)
        img_m_file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_m_name))

    conn = get_db()
    conn.execute('''INSERT INTO projects (title, short_desc, full_desc, skills_used, github_link, live_link, img_desktop, img_mobile, price) VALUES (?,?,?,?,?,?,?,?,?)''',
                 (request.form['title'], request.form['short_desc'], request.form['full_desc'], request.form['skills_used'], request.form['github_link'], request.form['live_link'], img_d_name, img_m_name, request.form.get('price', 0)))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/edit-project/<int:id>')
@login_required
def edit_project(id):
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id =?', (id,)).fetchone()
    conn.close()
    return render_template('edit-project.html', project=project)

@app.route('/edit-project/<int:id>', methods=['POST'])
@login_required
def update_project(id):
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id =?', (id,)).fetchone()
    img_d_name, img_m_name = project['img_desktop'], project['img_mobile']

    img_d_file = request.files.get('img_d')
    if img_d_file and img_d_file.filename!= '' and allowed_file(img_d_file.filename):
        if img_d_name: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img_d_name))
        img_d_name = secure_filename(img_d_file.filename)
        img_d_file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_d_name))

    img_m_file = request.files.get('img_m')
    if img_m_file and img_m_file.filename!= '' and allowed_file(img_m_file.filename):
        if img_m_name: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img_m_name))
        img_m_name = secure_filename(img_m_file.filename)
        img_m_file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_m_name))

    conn.execute('''UPDATE projects SET title=?, short_desc=?, full_desc=?, skills_used=?, github_link=?, live_link=?, img_desktop=?, img_mobile=?, price=? WHERE id=?''',
                 (request.form['title'], request.form['short_desc'], request.form['full_desc'], request.form['skills_used'], request.form['github_link'], request.form['live_link'], img_d_name, img_m_name, request.form.get('price', 0), id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/delete-project/<int:id>')
@login_required
def delete_project(id):
    conn = get_db()
    project = conn.execute('SELECT * FROM projects WHERE id =?', (id,)).fetchone()
    if project:
        if project['img_desktop']: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], project['img_desktop']))
        if project['img_mobile']: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], project['img_mobile']))
        conn.execute('DELETE FROM projects WHERE id =?', (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)