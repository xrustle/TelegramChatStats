from pymongo import MongoClient
from instabot.config import MONGO


class MongoDB:
    def __init__(self):
        client = MongoClient(**MONGO['uri'])
        self.db = client.get_database(MONGO['db'])

    def insert(self, record, coll_name='test'):
        collection = self.db[coll_name]
        collection.insert_one(record)


db = MongoDB()

if __name__ == "__main__":
    item = {"test": "test"}
    db.insert(item)
