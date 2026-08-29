from flask import Flask,render_template
app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/tasks.html')
def tasklist():
    mytasks = [
    {"id": 1, "text": "Task1", "done": False}, 
    {"id": 2, "text": "Task2", "done": False}
    ]
    return render_template('tasks.html', mytasks = mytasks)

if __name__ == "__main__":
    app.run(debug=True)
