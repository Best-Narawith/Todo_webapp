from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

mytasks = [
    {"id": 1, "text": "Task1", "done": False}, 
    {"id": 2, "text": "Task2", "done": False}
    ]
next_task_id = 3

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/tasks.html')
def tasklist():
    return render_template('tasks.html', mytasks = mytasks, task_count = len([t for t in mytasks if not t["done"]]))

@app.route('/add', methods=['POST'])
def add_tasks():
    global next_task_id
    task_name = request.form.get("new-task", "").strip()
    if task_name == "":
        return redirect(url_for('tasklist'))
    newtask = {
        "id" : next_task_id,
        "text" : task_name,
        "done" : False
    }
    mytasks.append(newtask)
    next_task_id += 1 
    return redirect(url_for('tasklist'))    

@app.route('/delete', methods=['POST'])
def delete_task():
    task_id = request.form.get('task_id', type=int)
    if task_id is None:
        return redirect(url_for('tasklist'))
    for task in mytasks:
        if task["id"] == task_id:
            mytasks.remove(task)
            break
    return redirect(url_for('tasklist'))

@app.route('/markdone', methods=['POST'])
def mark_done():
    done_ids = request.form.getlist('done')
    for task in mytasks:
        task["done"] = str(task["id"]) in done_ids
    return redirect(url_for('tasklist'))

if __name__ == "__main__":
    app.run(debug=True)
