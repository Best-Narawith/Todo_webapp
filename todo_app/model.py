from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

db = SQLAlchemy()

# SQLite ปิดการบังคับ foreign key เป็นค่าเริ่มต้น และ PRAGMA ต้องสั่งใหม่ทุก connection
# ไม่มีบรรทัดนี้ ForeignKey ใน model จะเป็นแค่คำอธิบาย ลบ user แล้ว task กลายเป็นแถวกำพร้า
@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):   # database อื่นไม่รู้จัก PRAGMA นี้
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

class Task(db.Model):
    __tablename__ = "todo_list"

    id = db.Column(db.Integer, primary_key = True)
    detail = db.Column(db.String(200), nullable = False)
    done = db.Column(db.Boolean, nullable = False, default = False, server_default=db.false())
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable = False)
    
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password_hash = db.Column(db.Text, nullable = False)

