import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_notes():
    r = client.get('/api/notes')
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

def test_create_note():
    payload = {"title":"pytest note","content":"<p>hello</p>","side_notes":["s1"]}
    r = client.post('/api/notes', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data.get('title') == 'pytest note'
    assert 'id' in data
