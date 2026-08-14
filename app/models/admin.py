from app.models.db import Database
from app.services.time_service import get_current_time
from bson import ObjectId

class AdminModel:
    @staticmethod
    def collection():
        return Database.get_db().admins

    @staticmethod
    def get_by_username(username):
        return AdminModel.collection().find_one({"username": username})

    @staticmethod
    def get_by_id(admin_id):
        return AdminModel.collection().find_one({"_id": ObjectId(admin_id)})

    @staticmethod
    def create(username, password_hash):
        now = get_current_time()
        record = {
            "username": username,
            "password_hash": password_hash,
            "role": "admin",
            "active": True,
            "created_at": now,
            "updated_at": now
        }
        try:
            res = AdminModel.collection().insert_one(record)
            return str(res.inserted_id)
        except Exception: # Handle duplicate key
            return None

    @staticmethod
    def update_password(admin_id, password_hash):
        AdminModel.collection().update_one(
            {"_id": ObjectId(admin_id)},
            {
                "$set": {
                    "password_hash": password_hash,
                    "updated_at": get_current_time()
                }
            }
        )
