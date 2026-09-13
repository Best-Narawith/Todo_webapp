from flask import render_template, request, redirect, url_for, session, jsonify, Blueprint
from model import db, Task, User
import database
MAX_DETAIL_LENGTH = 200

bp = Blueprint("tasks", __name__)

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


@bp.route('/tasks.html')
def tasklist():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for('auth.login'))
    return render_template('tasks.html')


@bp.route('/api/tasks', methods=['GET', 'POST'])
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
    mytasks = Task.query.filter_by(user_id=user_id).order_by(Task.id.asc()).all()
    mytasks_json = [{"id": task.id, "detail": task.detail, "done": task.done} for task in mytasks]
    return jsonify(mytasks_json)


@bp.route('/api/tasks/<int:task_id>', methods=['PATCH', 'DELETE'])
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