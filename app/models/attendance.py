from app.models.db import Database
from app.services.time_service import get_current_time
from bson import ObjectId

class AttendanceModel:
    @staticmethod
    def collection():
        return Database.get_db().attendance

    @staticmethod
    def get_by_id(record_id):
        try:
            return AttendanceModel.collection().find_one({"_id": ObjectId(record_id)})
        except Exception:
            return None

    @staticmethod
    def get_by_worker_and_date(worker_id, attendance_date):
        try:
            wid = ObjectId(worker_id) if isinstance(worker_id, str) else worker_id
        except Exception:
            return None
        return AttendanceModel.collection().find_one({
            "worker_id": wid,
            "attendance_date": attendance_date
        })

    @staticmethod
    def get_by_date(attendance_date):
        return list(AttendanceModel.collection().find({"attendance_date": attendance_date}))

    @staticmethod
    def get_worker_history(worker_id, start_date=None, end_date=None):
        query = {"worker_id": ObjectId(worker_id) if isinstance(worker_id, str) else worker_id}
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        if date_query:
            query["attendance_date"] = date_query
            
        return list(AttendanceModel.collection().find(query).sort("attendance_date", 1))

    @staticmethod
    def upsert_attendance(worker_id, attendance_date, status, admin_id):
        now = get_current_time()
        worker_oid = ObjectId(worker_id) if isinstance(worker_id, str) else worker_id
        admin_oid = ObjectId(admin_id) if isinstance(admin_id, str) else admin_id
        
        record = AttendanceModel.get_by_worker_and_date(worker_oid, attendance_date)
        
        if record:
            # Update existing
            AttendanceModel.collection().update_one(
                {"_id": record["_id"]},
                {
                    "$set": {
                        "status": status,
                        "updated_at": now,
                        "updated_by": admin_oid
                    }
                }
            )
            return str(record["_id"]), "updated", record["status"]
        else:
            # Create new
            new_record = {
                "worker_id": worker_oid,
                "attendance_date": attendance_date,
                "status": status,
                "recorded_at": now,
                "updated_at": now,
                "recorded_by": admin_oid,
                "updated_by": admin_oid
            }
            res = AttendanceModel.collection().insert_one(new_record)
            return str(res.inserted_id), "created", None
