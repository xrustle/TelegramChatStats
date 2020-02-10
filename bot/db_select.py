from pymongo import MongoClient
from bot.config import MONGO
from datetime import datetime


class MongoDB:
    def __init__(self):
        client = MongoClient(**MONGO['uri'])
        self.db = client.get_database(MONGO['db'])

    def get_user_chat_list(self, user_id):
        lst = {}
        chats = self.db['Members'].find({'users.id': user_id})
        for chat in chats:
            lst[chat['_id']] = chat['title']
        return lst

    def get_full_chat_list(self):
        lst = {}
        chats = self.db['Members'].find()
        for chat in chats:
            lst[chat['_id']] = chat['title']
        return lst

    def full_user_list(self):
        users = self.db['Members'].distinct('users.id')
        return users

    def most_commonly_used_words(self, chat_id, start=None, end=None, parts_of_speech=None):
        date_filter = {'$ne': datetime.strptime('01/01/70', '%d/%m/%y')}
        if start:
            date_filter['$gte'] = datetime.strptime(start, '%d/%m/%y')
        if end:
            date_filter['$lte'] = datetime.strptime(end, '%d/%m/%y')

        if parts_of_speech:
            pos_filter = {
                '$filter': {
                    'input': '$words',
                    'as': 'word',
                    'cond': {'$in': ['$$word.pos', parts_of_speech]}
                }
            }
        else:
            pos_filter = '$words'

        all_words = self.db['Chat' + str(chat_id)].aggregate(pipeline=[
            {  # Фильтруем по частям речи слова в массиве
                '$project': {
                    '_id': 0,
                    'words': pos_filter,
                    'date': '$date',
                    'from_id': '$from_id'
                }
            },
            {  # Разворачиваем массив слов в отдельные записи
                '$unwind': '$words'
            },
            {  # Убрать пустые
                '$match': {
                    'words': {
                        '$exists': True,
                        '$nin': [[], None]
                    },
                    'date': date_filter
                }
            },
            {  # Выносим поля
                '$addFields': {
                    'word': '$words.normal_form',
                    'pos': '$words.pos'
                }
            },
            {  # Удаляем массив
                '$unset': 'words'
            },
            {  # VOID
                '$unset': 'void pipeline'
            },
            {  # Группируем по словам и частям речи
                '$group': {
                    '_id': {
                        'word': '$word',
                        'pos': '$pos'
                    },
                    'count': {'$sum': 1}
                }
            },
            {  # Добавляем поля из _id
                '$addFields': {
                    'word': '$_id.word',
                    'pos': '$_id.pos'
                }
            },
            {  # Удаляем _id
                '$unset': '_id'
            },
            {  # Сортируем. Сверху будут наибольшие значения
                '$sort': {'count': -1}
            }
        ])

        for word in all_words:
            print(word)


db = MongoDB()

if __name__ == '__main__':
    # chat = '-397977949'  # J + D
    chat = '-396450692'  # work chat
    db.most_commonly_used_words(chat)
    # print(db.full_user_list())
