from flask import render_template,request,redirect,url_for,session,Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import database

bp = Blueprint("auth", __name__)

@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "" or password == "":
            return render_template('login.html', error = "กรุณากรอกชื่อและรหัสผ่าน ")
        conn = database.get_connection()
        try:
            c = conn.cursor()
            row = c.execute(" SELECT id,username,password_hash FROM users WHERE username = ?", (username,)).fetchone()
            if row and check_password_hash(row["password_hash"],password):
                session["user_id"] = row["id"]
                return redirect(url_for('tasks.tasklist'))
            else:
                return render_template('login.html', error = "รหัสผ่านไม่ถูกต้องหรือไม่พบชื่อผู้ใช้งาน")
        finally:
            conn.close()
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "" or password == "":
            return render_template('register.html', error = "กรุณากรอกชื่อและรหัสผ่าน ")
        hashed_password = generate_password_hash(password)
        conn = database.get_connection()
        try:
            c = conn.cursor()
            try:
                c.execute(""" INSERT INTO users (username,password_hash) VALUES (?, ?)
                """, (username, hashed_password))
                conn.commit()
            except sqlite3.IntegrityError:
                return render_template("register.html", error = "ชื่อนี้ถูกใช้แล้ว")
        finally:
            conn.close()
        return redirect(url_for('auth.login'))
    return render_template('register.html')