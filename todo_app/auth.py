from flask import render_template,request,redirect,url_for,session,Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from model import db, User
from sqlalchemy.exc import IntegrityError

bp = Blueprint("auth", __name__)

@bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "" or password == "":
            return render_template('login.html', error = "กรุณากรอกชื่อและรหัสผ่าน ")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for('tasks.tasklist'))
        else:
            return render_template('login.html', error = "รหัสผ่านไม่ถูกต้องหรือไม่พบชื่อผู้ใช้งาน")
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username == "" or password == "":
            return render_template('register.html', error = "กรุณากรอกชื่อและรหัสผ่าน ")
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