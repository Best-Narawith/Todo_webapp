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
def test_patch_done_validation(client,bad_value,expected_status_code):
    """Testing patch if done is non boolean"""
    client.post('/register', data = {'username': 'abc', 'password': 'def'}) #register
    client.post('/', data = {'username': 'abc', 'password': 'def'}) #login
    row = client.post('/api/tasks', json={'detail':"Sleep"}) #addtask
    task_id = row.get_json()['id']
    response = client.patch(f'/api/tasks/{task_id}', json={'done':bad_value}) 
    assert response.status_code == expected_status_code

def test_patch_rejects_missing_done(client):
    """PATCH must reject a request with no done field"""
    client.post('/register', data = {'username': 'abc', 'password': 'def'}) #register
    client.post('/', data = {'username': 'abc', 'password': 'def'}) #login
    row = client.post('/api/tasks', json={'detail':"Sleep"}) #addtask
    task_id = row.get_json()['id']
    response = client.patch(f'/api/tasks/{task_id}', json={'detail':'Eat'}) 
    assert response.status_code == 400
