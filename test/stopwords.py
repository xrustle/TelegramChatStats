from bot.db_select import db
from bot.config import CHATS
import collections
import csv


def most_commonly_used_words(chat_id):

    all_words = db.db['Chat' + str(chat_id)].aggregate(pipeline=[
        {  # Фильтруем по частям речи слова в массиве
            '$project': {
                '_id': 0,
                'words': '$words',
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

    return all_words


c = collections.Counter()

for chat in CHATS:
    words = most_commonly_used_words(chat)
    for word in words:
        c[(word['word'], word['pos'])] += word['count']


with open('eggs.csv', mode='w', newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    spamwriter.writerow(['word', 'pos', 'count'])
    for word in c.most_common():
        spamwriter.writerow([word[0][0], word[0][1], word[1]])
