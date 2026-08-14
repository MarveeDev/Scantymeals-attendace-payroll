from app.models.worker import WorkerModel
from app.models.salary_history import SalaryHistoryModel

def test_add_worker(auth_client, mock_db):
    data = {
        "staff_id": "EMP001",
        "full_name": "Ama Mensah",
        "phone": "0201234567",
        "role": "Worker",
        "date_joined": "2026-08-14",
        "weekly_salary": 200,
        "monthly_salary": 800
    }
    res = auth_client.post('/workers/add', data=data)
    assert res.status_code == 302 # redirect to list
    
    worker = list(WorkerModel.collection().find({"full_name": "Ama Mensah"}))[0]
    assert worker is not None
    assert worker["full_name"] == "Ama Mensah"
    assert worker["active"] is True
    assert "SM0" in worker["staff_id"]
    
    # Check salary history created
    hist = SalaryHistoryModel.get_history(worker["_id"])
    assert len(hist) == 1
    assert hist[0]["weekly_salary"] == 200

def test_add_worker_auto_id(auth_client, mock_db):
    data = {
        "full_name": "Kofi",
        "date_joined": "2026-08-14"
    }
    auth_client.post('/workers/add', data=data)
    
    data2 = {
        "full_name": "Duplicate",
        "date_joined": "2026-08-14"
    }
    res = auth_client.post('/workers/add', data=data2)
    assert res.status_code == 302 # Both are added, ID is auto-generated
    
def test_edit_worker(auth_client, mock_db):
    data = {
        "staff_id": "EMP003",
        "full_name": "Yaw",
        "date_joined": "2026-08-14",
        "weekly_salary": 200,
        "monthly_salary": 800
    }
    auth_client.post('/workers/add', data=data)
    worker = list(WorkerModel.collection().find({"full_name": "Yaw"}))[0]
    
    edit_data = {
        "full_name": "Yaw Updated",
        "weekly_salary": 250,
        "monthly_salary": 1000
    }
    auth_client.post(f'/workers/{worker["_id"]}/edit', data=edit_data)
    
    updated = list(WorkerModel.collection().find({"_id": worker["_id"]}))[0]
    assert updated["full_name"] == "Yaw Updated"
    assert updated["weekly_salary"] == 250
    
    hist = SalaryHistoryModel.get_history(updated["_id"])
    assert len(hist) == 2 # Initial + Edit
    assert hist[-1]["weekly_salary"] == 250

def test_deactivate_reactivate(auth_client, mock_db):
    data = {
        "staff_id": "EMP004",
        "full_name": "Esi",
        "date_joined": "2026-08-14"
    }
    auth_client.post('/workers/add', data=data)
    worker = list(WorkerModel.collection().find({"full_name": "Esi"}))[0]
    
    auth_client.post(f'/workers/{worker["_id"]}/deactivate')
    deact = WorkerModel.get_by_id(worker["_id"])
    assert deact["active"] is False
    assert deact["employment_end_date"] is not None
    
    auth_client.post(f'/workers/{worker["_id"]}/reactivate')
    react = WorkerModel.get_by_id(worker["_id"])
    assert react["active"] is True
    assert react["employment_end_date"] is None
