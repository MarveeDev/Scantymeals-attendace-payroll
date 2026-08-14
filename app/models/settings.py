from app.models.db import Database
from app.services.time_service import get_current_time
from bson import ObjectId

class SettingsModel:
    @staticmethod
    def collection():
        return Database.get_db().settings

    @staticmethod
    def get_settings():
        settings = SettingsModel.collection().find_one({"_id": "global_config"})
        if not settings:
            # Default settings
            settings = {
                "_id": "global_config",
                "default_weekly_salary": 200,
                "default_monthly_salary": 800,
                "absence_deduction_method": "fixed", # fixed, percentage, pro_rated
                "absence_deduction_value": 25, # GH₵25 or 25% or divisor
                "updated_at": get_current_time()
            }
            SettingsModel.collection().insert_one(settings)
        return settings

    @staticmethod
    def update_settings(data, admin_id):
        # Validate data types
        payload = {
            "default_weekly_salary": int(data.get("default_weekly_salary", 200)),
            "default_monthly_salary": int(data.get("default_monthly_salary", 800)),
            "absence_deduction_method": data.get("absence_deduction_method", "fixed"),
            "absence_deduction_value": float(data.get("absence_deduction_value", 25)),
            "updated_at": get_current_time()
        }
        
        try:
            payload["updated_by"] = ObjectId(admin_id) if isinstance(admin_id, str) and admin_id else admin_id
        except Exception:
            pass
        
        SettingsModel.collection().update_one(
            {"_id": "global_config"},
            {"$set": payload},
            upsert=True
        )
        return payload
