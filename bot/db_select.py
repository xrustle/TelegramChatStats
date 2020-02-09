from pymongo import MongoClient
from bot.config import MONGO, CHATS


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
        pipeline = []
        if start or end:
            pass

        if parts_of_speech:
            pipeline.append({  # Фильтруем по частям речи слова в массиве
                '$project': {
                    '_id': 0,
                    'words': {
                        '$filter': {
                            'input': '$words',
                            'as': 'word',
                            'cond': {'$in': ['$$word.pos', parts_of_speech]}
                        }
                    },
                    'date': '$date',
                    'from_id': '$from_date'
                }
            })
        else:
            pipeline.append({  # Фильтруем по частям речи слова в массиве
                '$project': {
                    '_id': 0,
                    'words': '$words',
                    'date': '$date',
                    'from_id': '$from_id'
                }
            })

        pipeline.extend([
            {  # Разворачиваем массив слов в отдельные записи
                '$unwind': '$words'
            },
            {  # Убрать пустые
                '$match': {
                    'words': {
                        '$exists': True,
                        '$nin': [[], None]
                    }
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

        all_words = self.db['Chat' + str(chat_id)].aggregate(pipeline=pipeline)
        for word in all_words:
            print(word)


db = MongoDB()

if __name__ == '__main__':
    # chat = '-397977949'  # J + D
    # chat = '-396450692'  # work chat
    # db.most_commonly_used_words(chat)
    print(db.full_user_list())
