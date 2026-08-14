import os
import sys
import logging
from flask import Flask
import mongomock

def run_debug():
    from run import app
    from app.models.db import Database
    
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    db = Database(mongomock.MongoClient('localhost', 27017), 'scantymeals_test')
    
    with app.test_client() as client:
        # Boot admin
        client.post('/login', data={'username': 'admin', 'password': 'password'})
        
        # Add worker
        client.post('/workers/add', data={
            "staff_id": "P1", "full_name": "Ama", "date_joined": "2026-08-01",
            "weekly_salary": 200, "monthly_salary": 800
        })
        
        from app.models.worker import WorkerModel
        worker = list(WorkerModel.collection().find({"full_name": "Ama"}))[0]
        
        res = client.post('/payroll/', data={
            "period_type": "Weekly",
            "start_date": "2026-08-01",
            "end_date": "2026-08-07",
            "worker_id": str(worker["_id"])
        }, follow_redirects=True)
        
        print(res.data.decode('utf-8'))

if __name__ == '__main__':
    run_debug()
