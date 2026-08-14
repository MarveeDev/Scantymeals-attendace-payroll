from app.models.db import Database
from app.services.time_service import get_current_time
from bson import ObjectId

class PayrollModel:
    @staticmethod
    def collection():
        return Database.get_db().payroll

    @staticmethod
    def get_by_id(payroll_id):
        try:
            return PayrollModel.collection().find_one({"_id": ObjectId(payroll_id)})
        except Exception:
            return None

    @staticmethod
    def get_by_worker_and_period(worker_id, period_start, period_end):
        return PayrollModel.collection().find_one({
            "worker_id": ObjectId(worker_id) if isinstance(worker_id, str) else worker_id,
            "period_start": period_start,
            "period_end": period_end
        })

    @staticmethod
    def check_overlap(worker_id, start_date, end_date):
        """Returns True if there is a finalized payroll that overlaps with the given dates."""
        worker_oid = ObjectId(worker_id) if isinstance(worker_id, str) else worker_id
        overlap_query = {
            "worker_id": worker_oid,
            "is_finalized": True,
            "$or": [
                {"period_start": {"$lte": end_date}, "period_end": {"$gte": start_date}}
            ]
        }
        return PayrollModel.collection().find_one(overlap_query) is not None

    @staticmethod
    def save_draft(data):
        now = get_current_time()
        worker_oid = ObjectId(data["worker_id"]) if isinstance(data["worker_id"], str) else data["worker_id"]
        
        # Check if draft exists for exact period
        existing = PayrollModel.get_by_worker_and_period(worker_oid, data["period_start"], data["period_end"])
        
        payload = {
            "worker_id": worker_oid,
            "period_type": data["period_type"],
            "period_start": data["period_start"],
            "period_end": data["period_end"],
            "salary_rate_used": str(data["salary_rate_used"]),
            "gross_amount": str(data["gross_amount"]),
            "eligible_days": int(data.get("eligible_days", 0)),
            "marked_days": int(data.get("marked_days", 0)),
            "present_days": int(data.get("present_days", 0)),
            "absent_days": int(data.get("absent_days", 0)),
            "not_marked_days": int(data.get("not_marked_days", 0)),
            "attendance_rate": float(data.get("attendance_rate", 0.0)),
            "absence_count": int(data["absence_count"]),
            "deduction_amount": str(data["deduction_amount"]),
            "net_amount": str(data["net_amount"]),
            "generated_at": get_current_time(),
            "is_finalized": False,
            "updated_at": now
        }
        
        if existing:
            if existing.get("is_finalized"):
                raise ValueError("Cannot overwrite finalized payroll")
            PayrollModel.collection().update_one({"_id": existing["_id"]}, {"$set": payload})
            return str(existing["_id"])
        else:
            payload["created_at"] = now
            res = PayrollModel.collection().insert_one(payload)
            return str(res.inserted_id)

    @staticmethod
    def finalize(payroll_id):
        try:
            PayrollModel.collection().update_one(
                {"_id": ObjectId(payroll_id)},
                {"$set": {"is_finalized": True, "updated_at": get_current_time()}}
            )
        except Exception:
            pass

    @staticmethod
    def get_worker_payroll(worker_id):
        worker_oid = ObjectId(worker_id) if isinstance(worker_id, str) else worker_id
        return list(PayrollModel.collection().find({"worker_id": worker_oid}).sort("period_start", -1))
