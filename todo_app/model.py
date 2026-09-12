from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Task(db.Model):
    __tablename__ = "todo_list"

    id = db.Column(db.Integer, primary_key = True)
    detail = db.Column(db.String(200), nullable = False)
    done = db.Column(db.Boolean, nullable = False, default = False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False )
    
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password_hash = db.Column(db.Text, nullable = False)

