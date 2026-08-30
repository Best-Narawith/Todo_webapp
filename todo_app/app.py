from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

mytasks = [
    {"id": 1, "text": "Task1", "done": False}, 
    {"id": 2, "text": "Task2", "done": False}
    ]
nextTaskId = 3

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/tasks.html')
def tasklist():
    return render_template('tasks.html', mytasks = mytasks)

@app.route('/add', methods=['POST'])
def add_tasks():
    global nextTaskId
    task_name = request.form.get("new-task", "").strip()
    if task_name == "":
        return redirect(url_for('tasklist'))
    newtask = {
        "id" : nextTaskId,
        "text" : task_name,
        "done" : False
    }
    mytasks.append(newtask)
    nextTaskId += 1 
    return redirect(url_for('tasklist'))    

if __name__ == "__main__":
    app.run(debug=True)
