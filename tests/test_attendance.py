from app.models.worker import WorkerModel
from app.models.attendance import AttendanceModel

def test_mark_attendance(auth_client, mock_db):
    data = {
        "staff_id": "EMP005",
        "full_name": "Ama",
        "date_joined": "2026-08-01"
    }
    auth_client.post('/workers/add', data=data)
    worker = list(WorkerModel.collection().find({"full_name": "Ama"}))[0]
    
    res = auth_client.post('/attendance/mark', data={
        "date": "2026-08-10",
        "worker_id": str(worker["_id"]),
        "status": "present"
    })
    
    att = AttendanceModel.get_by_worker_and_date(worker["_id"], "2026-08-10")
    assert att is not None
    assert att["status"] == "present"

def test_attendance_before_joined(auth_client, mock_db):
    data = {
        "staff_id": "EMP006",
        "full_name": "Kofi",
        "date_joined": "2026-08-15"
    }
    auth_client.post('/workers/add', data=data)
    worker = list(WorkerModel.collection().find({"full_name": "Kofi"}))[0]
    
    res = auth_client.post('/attendance/mark', data={
        "date": "2026-08-10", # Before joining
        "worker_id": str(worker["_id"]),
        "status": "present"
    }, follow_redirects=True)
    
    assert b"outside employment periods" in res.data
    att = AttendanceModel.get_by_worker_and_date(worker["_id"], "2026-08-10")
    assert att is None

def test_mark_all_present(auth_client, mock_db):
    auth_client.post('/workers/add', data={"staff_id": "A1", "full_name": "A", "date_joined": "2026-08-01"})
    auth_client.post('/workers/add', data={"staff_id": "A2", "full_name": "B", "date_joined": "2026-08-01"})
    
    auth_client.post('/attendance/mark_all', data={"date": "2026-08-10"})
    
    records = AttendanceModel.get_by_date("2026-08-10")
    assert len(records) == 2
    assert records[0]["status"] == "present"
