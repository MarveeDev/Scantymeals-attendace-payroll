import pytest
from app.services.attendance_service import AttendanceService
from app.models.worker import WorkerModel
from app.models.attendance import AttendanceModel
from datetime import date

def test_attendance_global_invariants(app, mock_db):
    """
    Tests Workers A-H to ensure the global attendance invariant:
    ELIGIBLE = PRESENT + ABSENT + NOT_MARKED
    and MARKED = PRESENT + ABSENT holds for all scenarios.
    """
    with app.app_context():
        # Setup Workers A-H
        # All tests will use August 2026 (2026-08-01 to 2026-08-31)
        start_date = date(2026, 8, 1)
        end_date = date(2026, 8, 31)

        # Worker A: Full month, 26 present, 5 absent, 0 not marked
        worker_a = {
            "staff_id": "SM_A", "full_name": "Worker A", "status": "active",
            "date_joined": "2026-08-01",
            "employment_periods": [{"start_date": "2026-08-01", "end_date": ""}]
        }
        wa_id = WorkerModel.create(worker_a)
        worker_a = WorkerModel.get_by_id(wa_id)
        
        for i in range(1, 32):
            d_str = f"2026-08-{i:02d}"
            status = "present" if i <= 26 else "absent"
            AttendanceModel.upsert_attendance(wa_id, d_str, status, "000000000000000000000000")

        summary_a = AttendanceService.get_period_summary(worker_a, start_date, end_date)
        assert summary_a["eligible_days"] == 31
        assert summary_a["present_days"] == 26
        assert summary_a["absent_days"] == 5
        assert summary_a["not_marked_days"] == 0

        # Worker B: Full month, 8 present, 2 absent, 21 not marked
        worker_b = {
            "staff_id": "SM_B", "full_name": "Worker B", "status": "active",
            "date_joined": "2026-08-01",
            "employment_periods": [{"start_date": "2026-08-01", "end_date": ""}]
        }
        wb_id = WorkerModel.create(worker_b)
        worker_b = WorkerModel.get_by_id(wb_id)
        
        for i in range(1, 9):
            AttendanceModel.upsert_attendance(wb_id, f"2026-08-{i:02d}", "present", "000000000000000000000000")
        for i in range(9, 11):
            AttendanceModel.upsert_attendance(wb_id, f"2026-08-{i:02d}", "absent", "000000000000000000000000")

        summary_b = AttendanceService.get_period_summary(worker_b, start_date, end_date)
        assert summary_b["eligible_days"] == 31
        assert summary_b["present_days"] == 8
        assert summary_b["absent_days"] == 2
        assert summary_b["not_marked_days"] == 21

        # Worker C: Joined mid-month (18 eligible), 1 present, 0 absent, 17 not marked
        worker_c = {
            "staff_id": "SM_C", "full_name": "Worker C", "status": "active",
            "date_joined": "2026-08-14",
            "employment_periods": [{"start_date": "2026-08-14", "end_date": ""}]
        }
        wc_id = WorkerModel.create(worker_c)
        worker_c = WorkerModel.get_by_id(wc_id)
        AttendanceModel.upsert_attendance(wc_id, "2026-08-14", "present", "000000000000000000000000")
        
        summary_c = AttendanceService.get_period_summary(worker_c, start_date, end_date)
        assert summary_c["eligible_days"] == 18
        assert summary_c["present_days"] == 1
        assert summary_c["absent_days"] == 0
        assert summary_c["not_marked_days"] == 17

        # Worker E & H: Employment gap and multiple periods
        # Aug 1-10, Aug 20-31
        worker_eh = {
            "staff_id": "SM_EH", "full_name": "Worker EH", "status": "active",
            "date_joined": "2026-08-01",
            "employment_periods": [
                {"start_date": "2026-08-01", "end_date": "2026-08-10"},
                {"start_date": "2026-08-20", "end_date": ""}
            ]
        }
        from bson.objectid import ObjectId
        weh_id = WorkerModel.create(worker_eh)
        WorkerModel.collection().update_one({"_id": ObjectId(weh_id)}, {"$set": {"employment_periods": worker_eh["employment_periods"]}})
        worker_eh = WorkerModel.get_by_id(weh_id)
        
        summary_eh = AttendanceService.get_period_summary(worker_eh, start_date, end_date)
        # 10 days + 12 days = 22 eligible days
        assert summary_eh["eligible_days"] == 22
        
        # Historical Test (Former Worker)
        worker_former = {
            "staff_id": "SM_FORMER", "full_name": "Worker Former", "status": "inactive",
            "date_joined": "2026-08-01",
            "employment_periods": [{"start_date": "2026-08-01", "end_date": "2026-08-31"}]
        }
        wf_id = WorkerModel.create(worker_former)
        WorkerModel.collection().update_one({"_id": ObjectId(wf_id)}, {"$set": {"employment_periods": worker_former["employment_periods"]}})
        worker_former = WorkerModel.get_by_id(wf_id)
        
        summary_f = AttendanceService.get_period_summary(worker_former, start_date, end_date)
        assert summary_f["eligible_days"] == 31

        # Test Custom Range Eligibility
        # Range: Aug 10 - Aug 20
        # Worker EH should have Aug 10 (1 day) and Aug 20 (1 day) eligible = 2 days
        custom_start = date(2026, 8, 10)
        custom_end = date(2026, 8, 20)
        summary_eh_custom = AttendanceService.get_period_summary(worker_eh, custom_start, custom_end)
        assert summary_eh_custom["eligible_days"] == 2
        
        # Verify custom range math invariant
        assert summary_eh_custom["eligible_days"] == summary_eh_custom["present_days"] + summary_eh_custom["absent_days"] + summary_eh_custom["not_marked_days"]
