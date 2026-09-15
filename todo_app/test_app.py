import os
import re
from model import db, Task, User
import tempfile
from pathlib import Path
import pytest

os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempfile.mkdtemp()) / 'test.db'}"  # ต้องมาก่อน
os.environ.pop("FLASK_DEBUG", None)
os.environ["SECRET_KEY"] = "test-secret-key"    
from app import app, resolve_secret_key                                                  # ค่อย import
app.config["WTF_CSRF_ENABLED"] = False   # ปิด CSRF เป็นค่าเริ่มต้นของเทส — เทสที่ตรวจ CSRF เปิดกลับเองด้วย monkeypatch
PASSWORD_TEST = "password123"

@app.route('/__boom')
def boom():
    """Test-only route: raises so the 500 handler can be exercised."""
    raise RuntimeError("boom")

@pytest.fixture
def client():
    """Provide a test client for the app.py"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            Task.query.delete()
            User.query.delete()
            db.session.commit()
        yield client

@pytest.fixture
def logged_in_client(client):
    """Provide a logged in user"""
    client.post('/register', data = {'username': 'abc', 'password': PASSWORD_TEST}) #register
    client.post('/', data = {'username': 'abc', 'password': PASSWORD_TEST}) #login
    return client


def test_register_creates_user(client):
    """Testing register"""
    response = client.post('/register', data = {'username': 'abc', 'password': PASSWORD_TEST})
    assert response.status_code == 302

def test_init_db_is_idempotent(client):
    """Testing init db is idempotent"""
    client.post('/register', data = {'username': 'ABC', 'password': PASSWORD_TEST})
    with app.app_context():
        db.create_all()
        row = User.query.filter_by(username="ABC").first()
    assert row is not None

@pytest.mark.parametrize("bad_value,expected_status_code", [
    (None, 400),
    ('false', 400),
    (True,200),
    (False,200)
])
def test_patch_done_validation(logged_in_client,bad_value,expected_status_code):
    """Testing patch if done is non boolean"""
    row = logged_in_client.post('/api/tasks', json={'detail':"Sleep"}) #addtask
    task_id = row.get_json()['id']
    response = logged_in_client.patch(f'/api/tasks/{task_id}', json={'done':bad_value}) 
    assert response.status_code == expected_status_code

def test_tasks_returned_in_creation_order(logged_in_client):
    """Check tasks return in creation order"""
    logged_in_client.post('/api/tasks', json={'detail':"Sleep"}) #addtask1
    logged_in_client.post('/api/tasks', json={'detail':"Eat"}) #addtask2
    logged_in_client.post('/api/tasks', json={'detail':"Play"}) #addtask3
    raw_data = logged_in_client.get('/api/tasks')
    data = raw_data.get_json()
    list_detail = [d["detail"] for d in data]
    assert list_detail == ['Sleep', 'Eat', 'Play']

@pytest.mark.parametrize("detail,expected_status_code",[
    ('ซักผ้า', 201),
    pytest.param(["a", "b"], 400, id="list"),
    pytest.param('a'*1000, 400, id="too_long"),
    pytest.param('a'*200, 201, id="edge"),
    pytest.param('a'*201, 400, id="off_edge_by_one"),
    (" ", 400),
    (123, 400),
    (None, 400),
    pytest.param({"x":1}, 400, id="dict")
])
def test_detail_validation(logged_in_client,detail,expected_status_code):
    """POST /api/tasks must validate the detail field"""
    response = logged_in_client.post('/api/tasks', json={"detail":detail})
    assert response.status_code == expected_status_code

@pytest.mark.parametrize("username,expected_status_code",[
    ("abc", 302),
    pytest.param("a"*80, 302, id="edge_length"),
    pytest.param("a"*81, 200, id="too_long"),
    pytest.param("", 200, id="empty"),
    pytest.param(" ", 200, id="whitespace"),
    pytest.param("a b", 200, id="contains_space"),
    pytest.param(" abc", 302, id="leading_space"),
    pytest.param("abc ", 302, id="trailing_space"),
    pytest.param(" abc ", 302, id="leading_trailing_space"),
])
def test_register_username_validation(client, username, expected_status_code):
    """POST /register must validate the username field"""
    response = client.post('/register', data = {'username': username, 'password': PASSWORD_TEST})
    assert response.status_code == expected_status_code
    with app.app_context():
        stored_user = User.query.filter_by(username=username.strip()).first() is not None
    assert stored_user == (expected_status_code == 302)

@pytest.mark.parametrize("password,expected_status_code",[
    ("abcdefgh", 302),
    pytest.param("a"*128, 302, id="upper_edge_length"),
    pytest.param("a"*129, 200, id="too_long"),
    pytest.param("a"*7, 200, id="too_short"),
    pytest.param("a"*8, 302, id="lower_edge_length"),
    pytest.param("", 200, id="empty"),
    pytest.param(" ", 200, id="whitespace"),
])
def test_register_password_validation(client, password, expected_status_code):
    """POST /register must validate the password field"""
    response = client.post('/register', data = {'username': 'abc', 'password': password})
    assert response.status_code == expected_status_code
    with app.app_context():
        stored_user = User.query.filter_by(username="abc").first() is not None
    assert stored_user == (expected_status_code == 302)

def test_patch_updates_detail(logged_in_client):
    """Test edit detail"""
    create_response = logged_in_client.post('/api/tasks', json={"detail": "Sleep"})
    task_id = create_response.get_json()["id"]
    patch_response = logged_in_client.patch(f'/api/tasks/{task_id}', json={"detail": "Eat"})
    data = logged_in_client.get('/api/tasks')
    edited_detail = data.get_json()[0]["detail"]
    assert patch_response.status_code == 200
    assert edited_detail == "Eat"

def test_patch_detail_keeps_done(logged_in_client):
    create_response = logged_in_client.post('/api/tasks', json={"detail": "Sleep"})
    task_id = create_response.get_json()["id"]
    logged_in_client.patch(f'/api/tasks/{task_id}', json={"done": True})
    patch_response = logged_in_client.patch(f'/api/tasks/{task_id}', json={"detail": "Eat"})
    data = logged_in_client.get('/api/tasks').get_json()[0]
    detail = data["detail"]
    done = data["done"]
    assert patch_response.status_code == 200
    assert detail == "Eat"
    assert done is True

def test_patch_done_keeps_detail(logged_in_client):
    create_response = logged_in_client.post('/api/tasks', json={"detail": "Sleep"})
    task_id = create_response.get_json()["id"]
    patch_response = logged_in_client.patch(f'/api/tasks/{task_id}', json={"done": True})
    data = logged_in_client.get('/api/tasks').get_json()[0]
    detail = data["detail"]
    done = data["done"]
    assert patch_response.status_code == 200
    assert done is True
    assert detail == "Sleep"

def test_patch_updates_both_fields(logged_in_client):
    create_response = logged_in_client.post('/api/tasks', json={"detail": "Sleep"})
    task_id = create_response.get_json()["id"]
    patch_response = logged_in_client.patch(f'/api/tasks/{task_id}', json={"detail": "Eat", "done": True})
    data = logged_in_client.get('/api/tasks').get_json()[0]
    detail = data["detail"]
    done = data["done"]
    assert patch_response.status_code == 200
    assert detail == "Eat"
    assert done is True

def test_patch_rejects_empty_body(logged_in_client):
    create_response = logged_in_client.post('/api/tasks', json={"detail": "Sleep"})
    task_id = create_response.get_json()["id"]
    patch_response = logged_in_client.patch(f'/api/tasks/{task_id}', json={})
    data = logged_in_client.get('/api/tasks').get_json()[0]
    detail = data["detail"]
    done = data["done"]
    assert patch_response.status_code == 400
    assert detail == "Sleep"
    assert done is False

@pytest.mark.parametrize("detail, expected_status_code", [
    ('ซักผ้า', 200),
    pytest.param(["a", "b"], 400, id="list"),
    pytest.param('a'*1000, 400, id="too_long"),
    pytest.param('a'*200, 200, id="edge"),
    pytest.param('a'*201, 400, id="off_edge_by_one"),
    (" ", 400),
    (123, 400),
    (None, 400),
    pytest.param({"x":1}, 400, id="dict")
])
def test_patch_detail_validation(logged_in_client,detail,expected_status_code):
    create_response = logged_in_client.post('/api/tasks', json={"detail": "Sleep"})
    task_id = create_response.get_json()["id"]
    patch_response = logged_in_client.patch(f'/api/tasks/{task_id}', json={"detail": detail})
    data = logged_in_client.get('/api/tasks').get_json()[0]
    stored_detail = data["detail"]
    assert patch_response.status_code == expected_status_code
    if expected_status_code == 400:
        assert stored_detail == "Sleep"

def test_patch_returns_updated_task(logged_in_client):
    create_response = logged_in_client.post('/api/tasks', json={"detail": "Sleep"})
    task_id = create_response.get_json()["id"]
    patch_response = logged_in_client.patch(f'/api/tasks/{task_id}', json={"done": True})
    assert patch_response.get_json()["done"] is True

def test_patch_missing_task_returns_404_before_validation(logged_in_client):
    patch_response = logged_in_client.patch('/api/tasks/999', json={"done": "Yes"})
    assert patch_response.status_code == 404

def test_404_error_handler(client):
    """Unknown URL renders our error page, not Flask's default"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    assert "Page not found" in response.text
    assert "Go back to the Login Page" in response.text

def test_500_error_handler(client):
    """Unhandled exception renders our error page with status 500"""
    # TESTING=True makes Flask re-raise exceptions into the test instead of
    # answering 500 — turn that off just for this request
    app.config["PROPAGATE_EXCEPTIONS"] = False
    try:
        response = client.get('/__boom')
    finally:
        app.config["PROPAGATE_EXCEPTIONS"] = None
    assert response.status_code == 500
    assert "Internal server error" in response.text

def test_api_404_still_json(logged_in_client):
    """The HTML 404 page must not leak into API responses"""
    response = logged_in_client.delete('/api/tasks/999')
    assert response.status_code == 404
    assert response.get_json() == {"error": "not found"}

def test_app_debug_mode_off():
    """Check that debug mode is off"""
    assert app.debug is False

@pytest.mark.parametrize("env_var,debug,expected", [
    (None, True, "dev-only-key"),
    ("my-secret", True, "my-secret"),
    ("my-secret", False, "my-secret"),
])
def test_resolve_secret_key_returns_expected(env_var, debug, expected):
    """Check that app returns expected secret key based on env_var and debug"""
    assert resolve_secret_key(env_var, debug) == expected

def test_app_raises_error_without_secret_key():
    """Check that app raises an error without secret key"""
    with pytest.raises(RuntimeError):
        resolve_secret_key(None, debug=False)

def test_session_cookie_has_samesite_and_httponly(client):
    """Check that session cookie has SameSite and HttpOnly attributes"""
    client.post('/register', data={'username': 'abc', 'password': PASSWORD_TEST})
    response = client.post('/', data={'username': 'abc', 'password': PASSWORD_TEST})
    cookie = response.headers.get('Set-Cookie')
    assert 'SameSite=Lax' in cookie
    assert 'HttpOnly' in cookie

def test_session_cookie_secure_flag_is_set(client, monkeypatch):
    """Check that session cookie has Secure attribute when SESSION_COOKIE_SECURE is set"""
    monkeypatch.setitem(app.config, "SESSION_COOKIE_SECURE", True)
    client.post('/register', data={'username': 'abc', 'password': PASSWORD_TEST})
    response = client.post('/', data={'username': 'abc', 'password': PASSWORD_TEST})
    cookie = response.headers.get('Set-Cookie')
    assert 'Secure' in cookie

def test_session_cookie_secure_flag_is_not_set(client, monkeypatch):
    """Check that session cookie does not have Secure attribute when SESSION_COOKIE_SECURE is not set"""
    monkeypatch.setitem(app.config, "SESSION_COOKIE_SECURE", False)
    client.post('/register', data={'username': 'abc', 'password': PASSWORD_TEST})
    response = client.post('/', data={'username': 'abc', 'password': PASSWORD_TEST})
    cookie = response.headers.get('Set-Cookie')
    assert 'Secure' not in cookie


def _csrf_token_from(client, path):
    """ดึงค่า csrf_token ที่ template ฝังไว้ในฟอร์มของหน้านั้น"""
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)

def test_register_rejects_missing_csrf_token(client, monkeypatch):
    """POST /register ต้องถูกปฏิเสธเมื่อไม่มี CSRF token"""
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    response = client.post('/register', data={'username': 'abc', 'password': PASSWORD_TEST})
    assert response.status_code == 400
    with app.app_context():
        assert User.query.filter_by(username="abc").first() is None

def test_register_accepts_valid_csrf_token(client, monkeypatch):
    """ฟอร์มจริงที่ฝัง token ไว้ต้องใช้งานได้ตามปกติ"""
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    token = _csrf_token_from(client, '/register')
    response = client.post('/register', data={'username': 'abc', 'password': PASSWORD_TEST, 'csrf_token': token})
    assert response.status_code == 302
    with app.app_context():
        assert User.query.filter_by(username="abc").first() is not None

def test_api_rejects_missing_csrf_token(logged_in_client, monkeypatch):
    """/api/* ก็ต้องการ token เหมือนกัน"""
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    response = logged_in_client.post('/api/tasks', json={'detail': 'ซักผ้า'})
    assert response.status_code == 400

def test_api_accepts_csrf_token_in_header(logged_in_client, monkeypatch):
    """app.js ส่ง token ทาง header X-CSRFToken"""
    monkeypatch.setitem(app.config, "WTF_CSRF_ENABLED", True)
    token = _csrf_token_from(logged_in_client, '/tasks.html')
    response = logged_in_client.post('/api/tasks', json={'detail': 'ซักผ้า'}, headers={'X-CSRFToken': token})
    assert response.status_code == 201

def test_logout_requires_post(logged_in_client):
    """GET /logout ต้องไม่ทำงาน — logout เปลี่ยนสถานะ ต้องเป็น POST"""
    assert logged_in_client.get('/logout').status_code == 405
    assert logged_in_client.post('/logout').status_code == 302
