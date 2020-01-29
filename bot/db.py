from pymongo import MongoClient
from bot.config import MONGO


class MongoDB:
    def __init__(self):
        client = MongoClient(**MONGO['uri'])
        self.db = client.get_database(MONGO['db'])

    def insert_message(self, chat_id, item, collection='Chat'):
        result = self.db[collection + str(chat_id)].update_one({'_id': item['id']},
                                                               {'$set': item},
                                                               upsert=True)
        return result.upserted_id


db = MongoDB()
