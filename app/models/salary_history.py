from app.models.db import Database
from app.services.time_service import get_current_time
from bson import ObjectId

class SalaryHistoryModel:
    @staticmethod
    def collection():
        return Database.get_db().salary_history

    @staticmethod
    def record_change(worker_id, weekly_salary, monthly_salary, effective_date, admin_id):
        worker_oid = ObjectId(worker_id) if isinstance(worker_id, str) else worker_id
        admin_oid = ObjectId(admin_id) if isinstance(admin_id, str) and admin_id else admin_id
        
        record = {
            "worker_id": worker_oid,
            "weekly_salary": int(weekly_salary),
            "monthly_salary": int(monthly_salary),
            "effective_date": effective_date,
            "created_at": get_current_time(),
            "created_by": admin_oid
        }
        
        SalaryHistoryModel.collection().insert_one(record)

    @staticmethod
    def get_history(worker_id):
        worker_oid = ObjectId(worker_id) if isinstance(worker_id, str) else worker_id
        return list(SalaryHistoryModel.collection().find({"worker_id": worker_oid}).sort("effective_date", -1))
