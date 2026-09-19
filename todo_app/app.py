from flask import Flask,render_template
import auth
import tasks
from model import db
import os
from pathlib import Path

app = Flask(__name__)
def resolve_secret_key(env_var, debug):
    if env_var is None:
        if debug is True:
            return "dev-only-key"
        else:
            raise RuntimeError("SECRET_KEY must be set in production")
    else:
        return env_var
app.secret_key = resolve_secret_key(os.environ.get("SECRET_KEY"), app.debug)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{Path(__file__).parent / 'todo.db'}")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE") == "1"
app.json.ensure_ascii = False  # type: ignore[attr-defined]
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
    app.run()
