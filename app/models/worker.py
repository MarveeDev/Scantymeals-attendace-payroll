from app.models.db import Database
from app.services.time_service import get_current_time
from bson import ObjectId

class WorkerModel:
    @staticmethod
    def collection():
        return Database.get_db().workers

    @staticmethod
    def _normalize(worker):
        if worker and "employment_periods" not in worker:
            worker["employment_periods"] = [{
                "start_date": worker.get("date_joined"),
                "end_date": worker.get("employment_end_date")
            }]
        return worker

    @staticmethod
    def get_by_id(worker_id):
        try:
            return WorkerModel._normalize(WorkerModel.collection().find_one({"_id": ObjectId(worker_id)}))
        except Exception:
            return None

    @staticmethod
    def get_by_staff_id(staff_id):
        return WorkerModel._normalize(WorkerModel.collection().find_one({"staff_id": staff_id}))

    @staticmethod
    def get_all(active_only=True):
        query = {"active": True} if active_only else {}
        workers = list(WorkerModel.collection().find(query).sort("full_name", 1))
        return [WorkerModel._normalize(w) for w in workers]

    @staticmethod
    def create(data):
        now = get_current_time()
        worker = {
            "staff_id": data["staff_id"],
            "full_name": data["full_name"],
            "phone": data.get("phone", ""),
            "role": data.get("role", "Worker"),
            "date_joined": data["date_joined"], # Expecting date string YYYY-MM-DD
            "employment_end_date": None,
            "employment_periods": [{"start_date": data["date_joined"], "end_date": None}],
            "active": True,
            "weekly_salary": int(data.get("weekly_salary", 200)),
            "monthly_salary": int(data.get("monthly_salary", 800)),
            "notes": data.get("notes", ""),
            "created_at": now,
            "updated_at": now
        }
        result = WorkerModel.collection().insert_one(worker)
        return str(result.inserted_id)

    @staticmethod
    def update(worker_id, data):
        data["updated_at"] = get_current_time()
        try:
            WorkerModel.collection().update_one(
                {"_id": ObjectId(worker_id)},
                {"$set": data}
            )
        except Exception:
            pass
    @staticmethod
    def deactivate(worker_id, end_date_str):
        worker = WorkerModel.get_by_id(worker_id)
        if not worker: return
        periods = worker["employment_periods"]
        if periods and periods[-1]["end_date"] is None:
            periods[-1]["end_date"] = end_date_str
        WorkerModel.update(worker_id, {
            "active": False,
            "employment_end_date": end_date_str,
            "employment_periods": periods
        })

    @staticmethod
    def reactivate(worker_id, start_date_str):
        worker = WorkerModel.get_by_id(worker_id)
        if not worker: return
        periods = worker["employment_periods"]
        if not periods or periods[-1]["end_date"] is not None:
            periods.append({"start_date": start_date_str, "end_date": None})
        WorkerModel.update(worker_id, {
            "active": True,
            "employment_end_date": None,
            "employment_periods": periods
        })
