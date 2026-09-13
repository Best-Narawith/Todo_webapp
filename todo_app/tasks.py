from flask import render_template, request, redirect, url_for, session, jsonify, Blueprint
from model import db, Task
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

def edit_data(data,task):
    if "done" not in data and "detail" not in data:
        return "missing data"
    if "done" in data:
        if not isinstance(data["done"],bool):
            return "done must be a boolean"
    if "detail" in data:
        detail_unstripped = data["detail"]
        detail, error = validate_detail(detail_unstripped)
        if error:
            return error
    if "done" in data:
        task.done = data["done"]
    if "detail" in data:
        task.detail = detail
    return None


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
        task = Task(user_id=user_id, detail=detail)
        db.session.add(task)
        db.session.commit()
        return jsonify({"id": task.id, "detail": task.detail, "done": task.done}), 201
    mytasks = Task.query.filter_by(user_id=user_id).order_by(Task.id.asc()).all()
    mytasks_json = [{"id": task.id, "detail": task.detail, "done": task.done} for task in mytasks]
    return jsonify(mytasks_json)


@bp.route('/api/tasks/<int:task_id>', methods=['PATCH', 'DELETE'])
def api_task_detail(task_id):
    user_id = session.get("user_id")
    if user_id is None:
        return jsonify({"error": "unauthorized"}), 401
    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if task is None:
        return jsonify({"error": "not found"}),404
    if request.method == 'DELETE':
        db.session.delete(task)
        db.session.commit()
        return jsonify({"deleted": task_id}), 200
    if request.method == 'PATCH':
        data = request.get_json(silent=True) or {}
        error = edit_data(data, task)
        if error:
            return jsonify({"error": error}), 400
        db.session.commit()
        return jsonify({"id": task.id, "detail": task.detail, "done": task.done}),200