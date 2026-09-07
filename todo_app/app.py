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
        if not isinstance(detail_unstripped, str):
            return jsonify({"error": "Value must be string"}),400
        detail = detail_unstripped.strip()
        if len(detail) > MAX_DETAIL_LENGTH:
            return jsonify({"error": "Too long value"}),400
        if detail == "":
            return jsonify({"error": "Value cannot be empty"}),400

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
        if "done" not in data:
            return jsonify({"error": "missing field: done"}),400
        if not isinstance(data["done"],bool):
            return jsonify({"error": "done must be a boolean"}),400
        done = data["done"]
        conn = database.get_connection()
        try:
            c = conn.cursor()
            c.execute("UPDATE todo_list SET done = ? WHERE user_id = ? AND id = ?", (done, user_id, task_id))
            if c.rowcount == 0:
                return jsonify({"error": "not found"}),404
            conn.commit()
        finally:
            conn.close()
        return jsonify({"task_id": task_id, "done": done}),200


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
