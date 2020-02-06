from pymongo import MongoClient
from bot.config import MONGO
import emoji
import regex
import re
from rnnmorph.predictor import RNNMorphPredictor


def handle_message(msg):
    data = {'handled': True}
    text = msg['raw'].get('message')
    if text:  # Обработка текста сообщения

        # Handling emoji
        words = regex.findall(r'\X', text)
        for word in words:
            if any(char in emoji.UNICODE_EMOJI for char in word):
                if 'emoticons' not in data:
                    data['emoticons'] = []
                data['emoticons'].append(word)

        # Handling russian words
        sentences = []
        for sentence in re.split(r'[.!?]+', text):
            word_list = re.findall(r'[а-яА-Я]', sentence)
            if word_list:
                sentences.append(word_list)
        if sentences:
            data['sentences'] = sentences
            pr_sentences = pr.predict_sentences(sentences=sentences)
            data['words'] = []
            for pr_sentence in pr_sentences:
                for pr_word in pr_sentence:
                    pr_handled_word = {'word': pr_word.word,
                                       'normal_form': pr_word.normal_form,
                                       'pos': pr_word.pos,
                                       'tag': pr_word.tag}
                    data['words'].append(pr_handled_word)

    return data


class MongoDB:
    def __init__(self):
        client = MongoClient(**MONGO['uri'])
        self.db = client.get_database(MONGO['db'])

    def insert_message(self, chat_id, msg, collection='Chat'):
        result = self.db[collection + str(chat_id)].update_one({'_id': msg['raw']['id']},
                                                               {'$set': msg},
                                                               upsert=True)
        return result.upserted_id

    def insert_member(self, chat_id, member, collection='Chat'):
        result = self.db[collection + str(chat_id)].update_one({'_id': member['id']},
                                                               {'$set': member},
                                                               upsert=True)
        return result.upserted_id

    def handle_new_messages(self):
        for collection_name in self.db.collection_names():
            if collection_name.startswith('Chat'):
                print('Обрабатываем сообщения чата', collection_name)
                new_messages = self.db[collection_name].find({})  # {'handled': {"$exists": False}})
                for message in new_messages:
                    handled_data = handle_message(message)
                    self.db[collection_name].update_one({'_id': message['raw']['id']},
                                                        {'$set': handled_data})

    def most_commonly_used_words(self, chat_id):
        all_words = self.db['Chat' + str(chat_id)].aggregate([
            {  # Фильтруем по частям речи слова в массиве
                '$project': {
                    '_id': 0,
                    # 'words': {
                    #     '$filter': {
                    #         'input': '$words',
                    #         'as': 'word',
                    #         'cond': {'$in': ['$$word.pos', ['NOUN']]}
                    #     }
                    # }
                    'words': '$words'
                }
            },
            {  # Разворачиваем массив слов в отдельные записи
                '$unwind': '$words'
            },
            {
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
            },
        ])
        for word in all_words:
            print(word)


db = MongoDB()
pr = RNNMorphPredictor()

if __name__ == '__main__':
    # chat = '-397977949'  # J + D
    chat = '-396450692'  # work chat
    db.most_commonly_used_words(chat)
