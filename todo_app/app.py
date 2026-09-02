from flask import Flask, render_template, request, redirect, url_for
import database

app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/tasks.html')
def tasklist():
    conn = database.get_connection()
    try:
        c = conn.cursor()
        c.execute(" SELECT id,detail,done FROM todo_list ")
        mytasks = c.fetchall()
    finally:
        conn.close()
    return render_template('tasks.html', mytasks = mytasks, task_count = len([t for t in mytasks if not t["done"]]))

@app.route('/add', methods=['POST'])
def add_tasks():
    detail = request.form.get("new-task", "").strip()
    if detail == "":
        return redirect(url_for('tasklist'))
    conn = database.get_connection()
    try:
        c = conn.cursor()
        c.execute(" INSERT INTO todo_list (detail) VALUES (?)", (detail,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('tasklist'))    

@app.route('/delete', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id', type=int)
    if task_id is None:
        return redirect(url_for('tasklist'))
    conn = database.get_connection()
    try:
        c = conn.cursor()
        c.execute("DELETE FROM todo_list WHERE id = ?", (task_id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('tasklist'))

@app.route('/markdone', methods=['POST'])
def mark_done():
    done_ids = request.form.getlist('done')
    conn = database.get_connection()
    try:
        c = conn.cursor()
        c.execute("UPDATE todo_list SET done = 0")
        for done_id in done_ids:
            c.execute("UPDATE todo_list SET done = 1 WHERE id = ?", (done_id,))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for('tasklist'))

if __name__ == "__main__":
    app.run(debug=True)
