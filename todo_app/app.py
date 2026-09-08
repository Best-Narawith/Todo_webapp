from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-key")
app.json.ensure_ascii = False
MAX_DETAIL_LENGTH = 200
database.init_db()

def validate_detail(detail_unstripped):
    if not isinstance(detail_unstripped, str):
        return None,"Value must be string"
    detail = detail_unstripped.strip()
    if len(detail) > MAX_DETAIL_LENGTH:
        return None,"Too long value"
    if detail == "":
        return None,"Value cannot be empty"
    return detail,None

def build_sql_script(data):
    if "done" not in data and "detail" not in data:
        return None, None, "missing data"
    set_part, values = [], []
    if "done" in data:
        if not isinstance(data["done"],bool):
            return None, None, "done must be a boolean"
        set_part.append('done = ?')
        values.append(data["done"])
    if "detail" in data:
        detail_unstripped = data.get("detail", "")
        detail, error = validate_detail(detail_unstripped)
        if error:
            return None, None, error
        set_part.append('detail = ?')
        values.append(detail)
    sql_script = "UPDATE todo_list SET " + ", ".join(set_part) + " WHERE user_id = ? AND id = ?"
    return sql_script, values, None

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
    return render_template('tasks.html')


@app.route('/api/tasks', methods=['GET', 'POST'])
def api_tasks():
    user_id = session.get("user_id")
    if user_id is None:
        return jsonify({"error": "unauthorized"}), 401

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        detail_unstripped = data.get("detail", "")
        detail, error = validate_detail(detail_unstripped)
        if error:
            return jsonify({"error": error}),400
        conn = database.get_connection()
        try:
            c = conn.cursor()
            c.execute(" INSERT INTO todo_list (user_id,detail) VALUES (?, ?) ", (user_id, detail,))
            conn.commit()
            return jsonify({"id": c.lastrowid, "detail": detail, "done": False}), 201
        finally:
            conn.close()    
    conn = database.get_connection()
    try:
        c = conn.cursor()
        c.execute(" SELECT id,detail,done FROM todo_list WHERE user_id=? ORDER BY id ASC",(user_id,))
        mytasks = c.fetchall()
        mytasks_json = [dict(task) for task in mytasks]
        for task in mytasks_json:
            task["done"] = bool(task["done"])
    finally:
        conn.close()
    return jsonify(mytasks_json)


@app.route('/api/tasks/<int:task_id>', methods=['PATCH', 'DELETE'])
def api_task_detail(task_id):
    user_id = session.get("user_id")
    if user_id is None:
        return jsonify({"error": "unauthorized"}), 401
    if request.method == 'DELETE':
        conn = database.get_connection()
        try:
            c = conn.cursor()
            c.execute("DELETE FROM todo_list WHERE id = ? and user_id = ?", (task_id, user_id))
            if c.rowcount == 0:
                return jsonify({"error": "not found"}),404
            conn.commit()
        finally:
            conn.close()
        return jsonify({"deleted": task_id}), 200
    if request.method == 'PATCH':
        data = request.get_json(silent=True) or {}
        sql_script, values, error = build_sql_script(data)
        if error:
            return jsonify({"error": error}), 400
        values.extend([user_id, task_id])
        conn = database.get_connection()
        try:
            c = conn.cursor()
            c.execute(sql_script, values)
            if c.rowcount == 0:
                return jsonify({"error": "not found"}),404
            conn.commit()
            updated_task = c.execute('SELECT id,detail,done FROM todo_list WHERE id = ? AND user_id = ?', (task_id,user_id)).fetchone()
        finally:
            conn.close()
        return jsonify({"id": updated_task["id"], "detail": updated_task["detail"], "done": bool(updated_task["done"])}),200


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
