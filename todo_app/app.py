from flask import Flask
import auth
import tasks
from model import db
import os
import database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", f"sqlite:///{database.DB_PATH}")
app.json.ensure_ascii = False
db.init_app(app)
app.register_blueprint(auth.bp)
app.register_blueprint(tasks.bp)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
