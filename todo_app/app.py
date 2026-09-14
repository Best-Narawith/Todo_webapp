from flask import Flask,render_template
import auth
import tasks
from model import db
import os
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{Path(__file__).parent / 'todo.db'}")
app.json.ensure_ascii = False
db.init_app(app)
app.register_blueprint(auth.bp)
app.register_blueprint(tasks.bp)

with app.app_context():
    db.create_all()

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error_handler.html", error = "Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("error_handler.html", error = "Internal server error"), 500

if __name__ == "__main__":
    app.run(debug=True)
