import pytest
import os
from mongomock import MongoClient
from run import create_app
from app.models.db import Database
from werkzeug.security import generate_password_hash

@pytest.fixture
def mock_db(monkeypatch):
    # Setup mongomock
    client = MongoClient()
    db = client.scantymeals_test
    
    # Mock the Database singleton
    monkeypatch.setattr(Database, 'client', client)
    monkeypatch.setattr(Database, 'db', db)
    
    # Create indexes for tests
    db.admins.create_index("username", unique=True)
    db.workers.create_index("staff_id", unique=True)
    db.attendance.create_index([("worker_id", 1), ("attendance_date", 1)], unique=True)
    db.payroll.create_index([("worker_id", 1), ("period_start", 1), ("period_end", 1)], unique=True)
    
    # Create a test admin
    db.admins.insert_one({
        "username": "testadmin",
        "password_hash": generate_password_hash("testpass"),
        "role": "admin",
        "active": True
    })
    
    return db

@pytest.fixture
def app(mock_db):
    os.environ['TESTING'] = 'True'
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test_secret"
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    client.post('/login', data={'username': 'testadmin', 'password': 'testpass'})
    return client
