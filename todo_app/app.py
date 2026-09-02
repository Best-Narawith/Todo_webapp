from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import database

app = Flask(__name__)
app.secret_key = "thisisthesecretkey"

@app.route('/', methods=['GET', 'POST'])
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
                return redirect(url_for('tasklist'))
            else:
                return render_template('login.html', error = "รหัสผ่านไม่ถูกต้องหรือไม่พบชื่อผู้ใช้งาน")
        finally:
            conn.close()
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/tasks.html')
def tasklist():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for('login'))
    conn = database.get_connection()
    try:
        c = conn.cursor()
        c.execute(" SELECT id,detail,done FROM todo_list WHERE user_id=?",(user_id,))
        mytasks = c.fetchall()
    finally:
        conn.close()
    return render_template('tasks.html', mytasks = mytasks, task_count = len([t for t in mytasks if not t["done"]]))


@app.route('/add', methods=['POST'])
def add_tasks():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for('login'))
    detail = request.form.get("new-task", "").strip()
    if detail == "":
        return redirect(url_for('tasklist'))
    conn = database.get_connection()
    try:
        c = conn.cursor()
        c.execute(" INSERT INTO todo_list (user_id,detail) VALUES (?, ?) ", (user_id, detail,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('tasklist'))    


@app.route('/delete', methods=['POST'])
def delete_task():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for('login'))
    task_id = request.form.get('task_id', type=int)
    if task_id is None:
        return redirect(url_for('tasklist'))
    conn = database.get_connection()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM todo_list WHERE id = ? and user_id = ?", (task_id, user_id))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('tasklist'))


@app.route('/markdone', methods=['POST'])
def mark_done():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for('login'))
    done_ids = request.form.getlist('done')
    conn = database.get_connection()
    try:
        c = conn.cursor()
        c.execute("UPDATE todo_list SET done = 0 WHERE user_id = ?", (user_id,))
        for done_id in done_ids:
            c.execute("UPDATE todo_list SET done = 1 WHERE id = ? AND user_id = ?", (done_id, user_id))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('tasklist'))


@app.route('/register', methods=['GET', 'POST'])
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
        return redirect(url_for('login'))
    return render_template('register.html')


if __name__ == "__main__":
    app.run(debug=True)
