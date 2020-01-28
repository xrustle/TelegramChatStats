from pymongo import MongoClient
from bot.config import MONGO


class MongoDB:
    def __init__(self):
        client = MongoClient(**MONGO['uri'])
        self.db = client.get_database(MONGO['db'])

    def insert_message(self, chat_id, item):
        result = self.db['Chat' + str(chat_id)].update_one({'_id': item['id']},
                                                           {'$set': item},
                                                           upsert=True)
        if result.upserted_id:
            print('Добавлено сообщение', item['id'], 'в чат', chat_id)
            return True
        else:
            print('Все сообщения чата', chat_id, 'обработаны')
            return False


db = MongoDB()
