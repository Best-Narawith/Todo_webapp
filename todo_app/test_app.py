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