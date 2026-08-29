from flask import Flask,render_template
app = Flask(__name__)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/tasks.html')
def tasklist():
    return render_template('tasks.html')

if __name__ == "__main__":
    app.run(debug=True)
