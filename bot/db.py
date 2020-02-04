from pymongo import MongoClient
from bot.config import MONGO
import emoji
import regex


def handle_message(msg):
    data = {'handled': True}
    text = msg.get('message')
    if text:
        # Handling emoji
        data['emoticons'] = []
        words = regex.findall(r'\X', text)
        for word in words:
            if any(char in emoji.UNICODE_EMOJI for char in word):
                data['emoticons'].append(word)
    return data


class MongoDB:
    def __init__(self):
        client = MongoClient(**MONGO['uri'])
        self.db = client.get_database(MONGO['db'])

    def insert_message(self, chat_id, item, collection='Chat'):
        result = self.db[collection + str(chat_id)].update_one({'_id': item['id']},
                                                               {'$set': item},
                                                               upsert=True)
        return result.upserted_id

    def handle_new_messages(self):
        for collection_name in self.db.collection_names():
            if collection_name.startswith('Chat'):
                print('Обрабатываем сообщения чата', collection_name)
                new_messages = self.db[collection_name].find({})  # {'handled': {"$exists": False}})
                for message in new_messages:
                    handled_data = handle_message(message)
                    self.db[collection_name].update_one({'_id': message['id']},
                                                        {'$set': handled_data})


db = MongoDB()

if __name__ == '__main__':
    chat = 'Chat-397977949'  # J + D
    new_messages = db.db[chat].find()
    for message in new_messages:
        handled_data = handle_message(message)
        db.db[chat].update_one({'_id': message['id']},
                               {'$set': handled_data})
