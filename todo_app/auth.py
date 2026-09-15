from flask import render_template,request,redirect,url_for,session,Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from model import db, User
from sqlalchemy.exc import IntegrityError
from collections import defaultdict
import time

bp = Blueprint("auth", __name__)
MAX_USERNAME_LENGTH = 80

# --- rate limit หน้า login ---
# นับ 2 แกนพร้อมกัน: ต่อ IP กัน password spraying · ต่อ username กัน brute-force จาก botnet
# เก็บในหน่วยความจำ = หายเมื่อ restart และแยกกันถ้ารันหลาย process (ของจริงต้องใช้ Redis)
LOGIN_WINDOW_SECONDS = 300
MAX_FAILED_PER_IP = 20
MAX_FAILED_PER_USER = 5

_failed_logins = defaultdict(list)   # key -> [เวลาที่ล้มเหลว, ...]

def _recent_failures(key, now):
    """คืนเวลาที่ล้มเหลวภายในหน้าต่างเวลา และทิ้งของเก่าออกจากหน่วยความจำไปด้วย"""
    recent = [t for t in _failed_logins[key] if t > now - LOGIN_WINDOW_SECONDS]
    if recent:
        _failed_logins[key] = recent
    else:
        _failed_logins.pop(key, None)
    return recent

def is_rate_limited(ip, username, now=None):
    now = time.time() if now is None else now
    if len(_recent_failures(f"ip:{ip}", now)) >= MAX_FAILED_PER_IP:
        return True
    if len(_recent_failures(f"user:{username}", now)) >= MAX_FAILED_PER_USER:
        return True
    return False

def record_failed_login(ip, username, now=None):
    now = time.time() if now is None else now
    _failed_logins[f"ip:{ip}"].append(now)
    _failed_logins[f"user:{username}"].append(now)

def clear_failed_logins(ip, username):
    _failed_logins.pop(f"ip:{ip}", None)
    _failed_logins.pop(f"user:{username}", None)

def validate_username(username):
    if " " in username:
        return None, "ชื่อผู้ใช้งานห้ามมีช่องว่าง"
    if len(username) > MAX_USERNAME_LENGTH:
        return None, "ชื่อผู้ใช้งานยาวเกินไป"
    return username, None

def validate_password(password):
    if len(password) < 8:
        return None, "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร"
    if len(password) > 128:
        return None, "รหัสผ่านยาวเกินไป"
    return password, None

@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "" or password == "":
            return render_template('login.html', error = "กรุณากรอกชื่อและรหัสผ่าน ")
        ip = request.remote_addr
        if is_rate_limited(ip, username):
            return render_template('login.html', error = "พยายามเข้าสู่ระบบบ่อยเกินไป กรุณารอสักครู่"), 429
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            clear_failed_logins(ip, username)
            session["user_id"] = user.id
            return redirect(url_for('tasks.tasklist'))
        else:
            record_failed_login(ip, username)
            return render_template('login.html', error = "รหัสผ่านไม่ถูกต้องหรือไม่พบชื่อผู้ใช้งาน")
    return render_template('login.html')


@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        raw_username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if raw_username == "" or password == "":
            return render_template('register.html', error = "กรุณากรอกชื่อผู้ใช้งานและรหัสผ่าน")
        username, error_username = validate_username(raw_username)
        if error_username:
            return render_template('register.html', error = error_username)
        password, error_password = validate_password(password)
        if error_password:
            return render_template('register.html', error = error_password)
        hashed_password = generate_password_hash(password)
        user = User(username=username, password_hash=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return render_template("register.html", error = "ชื่อนี้ถูกใช้แล้ว")
        return redirect(url_for('auth.login'))
    return render_template('register.html')