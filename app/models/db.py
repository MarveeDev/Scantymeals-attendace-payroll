import os
from pymongo import MongoClient

class Database:
    client = None
    db = None

    @classmethod
    def initialize(cls):
        uri = os.getenv('MONGODB_URI')
        db_name = os.getenv('MONGODB_DATABASE', 'scantymeals_staff')
        
        if not uri:
            raise ValueError("MONGODB_URI environment variable is not set")
            
        cls.client = MongoClient(uri)
        cls.db = cls.client[db_name]
        
    @classmethod
    def get_db(cls):
        if cls.db is None:
            cls.initialize()
        return cls.db

def init_db(app):
    """Initializes the database and creates necessary indexes."""
    db = Database.get_db()
    
    # Create indexes based on the master specification
    db.admins.create_index("username", unique=True)
    db.workers.create_index("staff_id", unique=True)
    db.attendance.create_index([("worker_id", 1), ("attendance_date", 1)], unique=True)
    db.payroll.create_index([("worker_id", 1), ("period_start", 1), ("period_end", 1)], unique=True)
    db.payments.create_index("worker_id")
    db.audit_logs.create_index("timestamp")
