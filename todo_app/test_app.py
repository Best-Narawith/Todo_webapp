import tempfile
from pathlib import Path
import database
import pytest

database.DB_PATH = Path(tempfile.mkdtemp()) / "test.db"   # ต้องมาก่อน
from app import app                                                  # ค่อย import

@pytest.fixture
def client():
    """Provide a test client for the app.py"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        conn = database.get_connection()
        conn.executescript(" DELETE FROM todo_list; DELETE FROM users")
        conn.commit()
        conn.close()
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
    database.init_db()
    conn = database.get_connection()
    row = conn.execute(" SELECT username FROM users WHERE username = ?", ("ABC",)).fetchone()
    conn.close()
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

def test_patch_rejects_missing_done(logged_in_client):
    """PATCH must reject a request with no done field"""
    row = logged_in_client.post('/api/tasks', json={'detail':"Sleep"}) #addtask
    task_id = row.get_json()['id']
    response = logged_in_client.patch(f'/api/tasks/{task_id}', json={'detail':'Eat'}) 
    assert response.status_code == 400

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
    response = logged_in_client.post('/api/tasks', json={"detail":detail,})
    assert response.status_code == expected_status_code