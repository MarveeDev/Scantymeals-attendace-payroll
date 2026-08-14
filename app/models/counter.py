from app.models.db import Database

class CounterModel:
    @staticmethod
    def collection():
        return Database.get_db().counters

    @staticmethod
    def get_next_sequence(counter_id):
        # find_one_and_update is atomic
        ret = CounterModel.collection().find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"sequence": 1}},
            upsert=True,
            return_document=True
        )
        return ret["sequence"]

    @staticmethod
    def init_sequence(counter_id, initial_value):
        # only sets it if it doesn't exist, or we can use $max to safely push it up
        CounterModel.collection().update_one(
            {"_id": counter_id},
            {"$max": {"sequence": initial_value}},
            upsert=True
        )
