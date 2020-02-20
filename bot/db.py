from pymongo import MongoClient
from bot.config import MONGO
import emoji
import regex
import re
from rnnmorph.predictor import RNNMorphPredictor


class MongoDB:
    def __init__(self):
        client = MongoClient(**MONGO['uri'])
        self.db = client.get_database(MONGO['db'])

    def insert_message(self, chat_id, msg, collection='Chat'):
        _id = msg['_id']
        del msg['_id']
        result = self.db[collection + str(chat_id)].update_one({'_id': _id},
                                                               {'$set': msg},
                                                               upsert=True)
        return result.raw_result['updatedExisting']

    def insert_members(self, chat, members):
        result = self.db['Members'].update_one({'_id': str(chat)},
                                               {'$set': members},
                                               upsert=True)
        return result.upserted_id

    @staticmethod
    def handle_message(msg, pr):
        data = {'handled': True}
        text = msg.get('message')
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
            for sentence in re.split(r'[.!?]+', re.sub(r'[ёЁ]', 'е', text)):
                word_list = re.findall(r'[а-яА-ЯёЁ]+-[а-яА-ЯёЁ]+|[а-яА-ЯёЁ]+', sentence)
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

    def handle_new_messages(self):
        pr = RNNMorphPredictor()
        for collection_name in self.db.collection_names():
            if collection_name.startswith('Chat'):
                print('Обрабатываем сообщения чата', collection_name)
                new_messages = self.db[collection_name].find({'handled': {"$exists": False}})
                for message in new_messages:
                    handled_data = self.handle_message(message, pr)
                    self.db[collection_name].update_one({'_id': message['_id']},
                                                        {'$set': handled_data})


db = MongoDB()
