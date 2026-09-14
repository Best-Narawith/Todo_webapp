import os
from model import db, Task, User
import tempfile
from pathlib import Path
import pytest

os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempfile.mkdtemp()) / 'test.db'}"  # ต้องมาก่อน
from app import app                                                  # ค่อย import

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
    client.post('/register', data = {'username': 'abc', 'password': 'def'}) #register
    client.post('/', data = {'username': 'abc', 'password': 'def'}) #login
    return client


def test_register_creates_user(client):
    """Testing register"""
    response = client.post('/register', data = {'username': 'abc', 'password': 'def'})
    assert response.status_code == 302

def test_init_db_is_idempotent(client):
    """Testing init db is idempotent"""
    client.post('/register', data = {'username': 'ABC', 'password': 'DEF'})
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
    response = client.post('/register', data = {'username': username, 'password': 'def'})
    assert response.status_code == expected_status_code
    with app.app_context():
        stored_user = User.query.filter_by(username=username.strip()).first() is not None
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
