from app.models.worker import WorkerModel
from app.models.attendance import AttendanceModel
from app.models.payroll import PayrollModel
from app.models.settings import SettingsModel

def test_payroll_calculation(auth_client, mock_db):
    auth_client.post('/workers/add', data={
        "staff_id": "P1", "full_name": "Ama", "date_joined": "2026-08-01",
        "weekly_salary": 200, "monthly_salary": 800
    })
    worker = list(WorkerModel.collection().find({"full_name": "Ama"}))[0]
    
    # Set default settings (Fixed deduction of 25)
    SettingsModel.update_settings({
        "absence_deduction_method": "fixed",
        "absence_deduction_value": 25
    }, "000000000000000000000000")
    
    # Mark attendance
    AttendanceModel.upsert_attendance(worker["_id"], "2026-08-01", "present", "000000000000000000000000")
    AttendanceModel.upsert_attendance(worker["_id"], "2026-08-02", "absent", "000000000000000000000000")
    
    # Generate payroll Weekly
    res = auth_client.post('/payroll/', data={
        "period_type": "Weekly",
        "start_date": "2026-08-01",
        "end_date": "2026-08-07",
        "worker_id": str(worker["_id"])
    }, follow_redirects=True)
    
    print("DEBUG DATA:", res.data.decode('utf-8'))
    assert b"Draft payroll generated" in res.data
    
    payrolls = list(PayrollModel.collection().find({"worker_id": worker["_id"]}))
    assert len(payrolls) == 1
    p = payrolls[0]
    
    assert p["gross_amount"] == "200.00"
    assert p["absence_count"] == 1
    assert p["deduction_amount"] == "25.00" # 1 * 25
    assert p["net_amount"] == "175.00"
    assert p["is_finalized"] is False

def test_payroll_overlap_protection(auth_client, mock_db):
    auth_client.post('/workers/add', data={
        "full_name": "Kofi", "date_joined": "2026-08-01"
    })
    worker = list(WorkerModel.collection().find({"full_name": "Kofi"}))[0]
    
    # Generate and finalize 1-7
    auth_client.post('/payroll/', data={
        "period_type": "Weekly",
        "start_date": "2026-08-01",
        "end_date": "2026-08-07",
        "worker_id": str(worker["_id"])
    })
    p1 = PayrollModel.collection().find_one({"worker_id": worker["_id"]})
    auth_client.post(f'/payroll/{p1["_id"]}/finalize')
    
    # Attempt to generate 5-10
    res = auth_client.post('/payroll/', data={
        "period_type": "Custom",
        "start_date": "2026-08-05",
        "end_date": "2026-08-10",
        "worker_id": str(worker["_id"])
    }, follow_redirects=True)
    
    assert b"Overlapping finalized payroll exists" in res.data
    
    # Attempt to generate 8-14 (should pass)
    res2 = auth_client.post('/payroll/', data={
        "period_type": "Weekly",
        "start_date": "2026-08-08",
        "end_date": "2026-08-14",
        "worker_id": str(worker["_id"])
    }, follow_redirects=True)
    
    assert b"Draft payroll generated" in res2.data
    assert PayrollModel.collection().count_documents({"worker_id": worker["_id"]}) == 2

def test_percentage_deduction(auth_client, mock_db):
    auth_client.post('/workers/add', data={
        "full_name": "Yaw", "date_joined": "2026-08-01",
        "weekly_salary": 200
    })
    worker = list(WorkerModel.collection().find({"full_name": "Yaw"}))[0]
    
    SettingsModel.update_settings({
        "absence_deduction_method": "percentage",
        "absence_deduction_value": 10 # 10%
    }, "000000000000000000000000")
    
    AttendanceModel.upsert_attendance(worker["_id"], "2026-08-01", "absent", "000000000000000000000000")
    
    auth_client.post('/payroll/', data={
        "period_type": "Weekly",
        "start_date": "2026-08-01",
        "end_date": "2026-08-07",
        "worker_id": str(worker["_id"])
    })
    
    p = PayrollModel.collection().find_one({"worker_id": worker["_id"]})
    assert p["gross_amount"] == "200.00"
    assert p["deduction_amount"] == "20.00" # 10% of 200
    assert p["net_amount"] == "180.00"

def test_attendance_scenarios(auth_client, mock_db):
    from app.services.attendance_service import AttendanceService
    from datetime import date
    
    # Setup worker full month
    auth_client.post('/workers/add', data={
        "full_name": "FullMonth", "date_joined": "2026-08-01"
    })
    worker_full = list(WorkerModel.collection().find({"full_name": "FullMonth"}))[0]
    
    for i in range(1, 27): # 26 present
        AttendanceModel.upsert_attendance(worker_full["_id"], f"2026-08-{i:02d}", "present", "000000000000000000000000")
    for i in range(27, 32): # 5 absent
        AttendanceModel.upsert_attendance(worker_full["_id"], f"2026-08-{i:02d}", "absent", "000000000000000000000000")
        
    summary = AttendanceService.get_monthly_summary(worker_full, 2026, 8)
    assert summary["eligible_days"] == 31
    assert summary["marked_days"] == 31
    assert summary["present_days"] == 26
    assert summary["absent_days"] == 5
    assert summary["not_marked_days"] == 0
    assert summary["attendance_rate"] == 83.87
    
    # Mid-month join
    auth_client.post('/workers/add', data={
        "full_name": "MidMonth", "date_joined": "2026-08-10"
    })
    worker_mid = list(WorkerModel.collection().find({"full_name": "MidMonth"}))[0]
    summary_mid = AttendanceService.get_monthly_summary(worker_mid, 2026, 8)
    assert summary_mid["eligible_days"] == 22
    
    # Mid-month departure
    auth_client.post('/workers/add', data={
        "full_name": "Departed", "date_joined": "2026-08-01"
    })
    worker_dep = list(WorkerModel.collection().find({"full_name": "Departed"}))[0]
    WorkerModel.deactivate(worker_dep["_id"], "2026-08-20")
    worker_dep = WorkerModel.get_by_id(worker_dep["_id"])
    summary_dep = AttendanceService.get_monthly_summary(worker_dep, 2026, 8)
    assert summary_dep["eligible_days"] == 20
    
    # Employment Gap
    auth_client.post('/workers/add', data={
        "full_name": "Gap", "date_joined": "2026-08-01"
    })
    worker_gap = list(WorkerModel.collection().find({"full_name": "Gap"}))[0]
    WorkerModel.deactivate(worker_gap["_id"], "2026-08-10")
    WorkerModel.reactivate(worker_gap["_id"], "2026-08-20")
    worker_gap = WorkerModel.get_by_id(worker_gap["_id"])
    
    summary_gap = AttendanceService.get_monthly_summary(worker_gap, 2026, 8)
    # Aug 1-10 (10) + Aug 20-31 (12) = 22
    assert summary_gap["eligible_days"] == 22
    
    # Leap year (Feb 2028)
    auth_client.post('/workers/add', data={
        "full_name": "Leap", "date_joined": "2028-02-01"
    })
    worker_leap = list(WorkerModel.collection().find({"full_name": "Leap"}))[0]
    summary_leap = AttendanceService.get_monthly_summary(worker_leap, 2028, 2)
    assert summary_leap["eligible_days"] == 29
