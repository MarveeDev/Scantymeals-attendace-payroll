from app.models.db import Database
from app.services.time_service import get_current_time
from bson import ObjectId

class AuditModel:
    @staticmethod
    def collection():
        return Database.get_db().audit_logs

    @staticmethod
    def log(admin_id, action, entity_type, entity_id, previous_value=None, new_value=None, metadata=None):
        admin_oid = ObjectId(admin_id) if isinstance(admin_id, str) and admin_id else admin_id
        
        log_entry = {
            "admin_id": admin_oid,
            "action": action,
            "entity_type": entity_type,
            "entity_id": str(entity_id) if entity_id else None,
            "previous_value": previous_value,
            "new_value": new_value,
            "timestamp": get_current_time(),
            "metadata": metadata or {}
        }
        
        AuditModel.collection().insert_one(log_entry)

    @staticmethod
    def get_recent(limit=50):
        return list(AuditModel.collection().find().sort("timestamp", -1).limit(limit))
