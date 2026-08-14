from app.models.db import Database
from app.services.time_service import get_current_time
from bson import ObjectId

class PaymentModel:
    @staticmethod
    def collection():
        return Database.get_db().payments

    @staticmethod
    def record_payment(data):
        worker_oid = ObjectId(data["worker_id"]) if isinstance(data["worker_id"], str) else data["worker_id"]
        payroll_oid = ObjectId(data["payroll_id"]) if data.get("payroll_id") and isinstance(data["payroll_id"], str) else data.get("payroll_id")
        admin_oid = ObjectId(data["recorded_by"]) if isinstance(data["recorded_by"], str) and data["recorded_by"] else data["recorded_by"]
        
        record = {
            "worker_id": worker_oid,
            "payroll_id": payroll_oid,
            "amount": int(data["amount"]),
            "payment_date": data["payment_date"],
            "payment_method": data["payment_method"],
            "reference": data.get("reference", ""),
            "notes": data.get("notes", ""),
            "recorded_by": admin_oid,
            "created_at": get_current_time()
        }
        
        res = PaymentModel.collection().insert_one(record)
        return str(res.inserted_id)

    @staticmethod
    def get_by_worker(worker_id):
        worker_oid = ObjectId(worker_id) if isinstance(worker_id, str) else worker_id
        return list(PaymentModel.collection().find({"worker_id": worker_oid}).sort("payment_date", -1))
