from flask import Flask
import auth
import tasks
import os
import database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-key")
app.json.ensure_ascii = False
app.register_blueprint(auth.bp)
app.register_blueprint(tasks.bp)

database.init_db()

if __name__ == "__main__":
    app.run(debug=True)
