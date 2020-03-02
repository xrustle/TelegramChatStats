import mysql.connector
from bot.config import MYSQL
import emoji
import regex
import re
from rnnmorph.predictor import RNNMorphPredictor


class MySQL:
    def __init__(self):
        self.mydb = mysql.connector.connect(
            host=MYSQL['host'],
            user=MYSQL['user'],
            password=MYSQL['password']
            # auth_plugin='mysql_native_password'
        )
        self.mycursor = self.mydb.cursor()
        self.mycursor.execute(f'CREATE DATABASE if NOT EXISTS {MYSQL["database"]}')

        self.mydb = mysql.connector.connect(**MYSQL)
        self.mycursor = self.mydb.cursor()

        self.mycursor.execute(
            "CREATE TABLE IF NOT EXISTS chats ("
            "  id int(10) unsigned NOT NULL AUTO_INCREMENT,"
            "  chat_id varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  name varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  PRIMARY KEY (id)"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
        )
        self.mycursor.execute(
            "CREATE TABLE IF NOT EXISTS messages ("
            "  id int(10) unsigned NOT NULL AUTO_INCREMENT,"
            "  chat_id int(10) unsigned NOT NULL,"
            "  msg_id varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  user_id int(10) unsigned NOT NULL,"
            "  creation_date datetime,"
            "  text text CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  handled BOOLEAN,"
            "  PRIMARY KEY (id)"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
        )
        self.mycursor.execute(
            "CREATE TABLE IF NOT EXISTS words ("
            "  id int(10) unsigned NOT NULL AUTO_INCREMENT,"
            "  message_id int(10) unsigned NOT NULL,"
            "  word varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  normal_form varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  pos varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  tag varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  PRIMARY KEY (id)"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
        )
        self.mycursor.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "  id int(10) unsigned NOT NULL AUTO_INCREMENT,"
            "  chat_id int(10) unsigned NOT NULL,"
            "  user_id varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  name varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,"
            "  first_name varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,"
            "  last_name varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,"
            "  username varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin,"
            "  PRIMARY KEY (id)"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
        )
        self.mycursor.execute(
            "CREATE TABLE IF NOT EXISTS emoticons ("
            "  id int(10) unsigned NOT NULL AUTO_INCREMENT,"
            "  message_id int(10) unsigned NOT NULL,"
            "  emoticon varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,"
            "  PRIMARY KEY (id)"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
        )
        self.full_chat_list = self.get_full_chat_list()
        self.full_user_list = self.get_full_user_list()

    def insert_chat(self, chat_id, chat_name):
        self.mycursor.execute("SELECT id FROM chats WHERE chat_id = %s", (chat_id,))
        chat_record = self.mycursor.fetchone()
        if not chat_record:
            self.mycursor.execute("INSERT INTO chats (chat_id, name) VALUES (%s, %s);", (chat_id, chat_name))
            self.mydb.commit()
            return self.mycursor.lastrowid
        return chat_record[0]

    def insert_message(self, chat_id, msg_id, msg_date, text, sender):
        self.mycursor.execute("SELECT id FROM messages WHERE chat_id = %s AND msg_id = %s", (chat_id, msg_id))
        if not self.mycursor.fetchone():
            self.mycursor.execute("INSERT INTO messages (chat_id, msg_id, user_id, creation_date, text) "
                                  "VALUES (%s, %s, %s, %s, %s)", (chat_id, msg_id, sender, msg_date, text))
            self.mydb.commit()
            return True
        else:
            return False

    def insert_user(self, chat_id, user_id, first_name=None, last_name=None, username=None, name=None):
        self.mycursor.execute("SELECT id FROM users WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
        user_record = self.mycursor.fetchone()
        if not user_record:
            self.mycursor.execute("INSERT INTO users (chat_id, user_id, name, first_name, last_name, username) "
                                  "VALUES (%s, %s, %s, %s, %s, %s)",
                                  (chat_id, user_id, name, first_name, last_name, username))
            self.mydb.commit()
            return self.mycursor.lastrowid
        return user_record[0]

    def handle_new_messages(self):
        pr = RNNMorphPredictor()
        self.mycursor.execute("SELECT id, text FROM messages WHERE handled IS NULL")
        message_records = self.mycursor.fetchall()
        emoticons_count = 0
        words_count = 0
        for message_record in message_records:
            msg_id, text = message_record
            if text:
                emoticons = regex.findall(r'\X', text)
                for emoticon in emoticons:
                    if any(char in emoji.UNICODE_EMOJI for char in emoticon):
                        self.mycursor.execute(f"INSERT INTO emoticons (message_id, emoticon) VALUES (%s, %s);",
                                              (msg_id, emoticon))
                        emoticons_count += 1
                sentences = []
                for sentence in re.split(r'[.!?]+', re.sub(r'[ёЁ]', 'е', text)):
                    word_list = re.findall(r'[а-яА-ЯёЁ]+-[а-яА-ЯёЁ]+|[а-яА-ЯёЁ]+', sentence)
                    if word_list:
                        sentences.append(word_list)
                if sentences:
                    pr_sentences = pr.predict_sentences(sentences=sentences)
                    for pr_sentence in pr_sentences:
                        for pr_word in pr_sentence:
                            self.mycursor.execute(f"INSERT INTO words (message_id, word, normal_form, pos, tag) "
                                                  f"VALUES (%s, %s, %s, %s, %s);",
                                                  (msg_id, pr_word.word, pr_word.normal_form, pr_word.pos, pr_word.tag))
                            words_count += 1
            self.mycursor.execute("UPDATE messages SET handled = %s WHERE id = %s", (True, message_record[0]))
            self.mydb.commit()
        return len(message_records), words_count, emoticons_count

    def get_full_chat_list(self):
        self.mycursor.execute("SELECT id, name FROM chats")
        chat_records = self.mycursor.fetchall()
        dct = {}
        for chat_record in chat_records:
            dct[chat_record[0]] = chat_record[1]
        return dct

    def update_full_chat_list(self):
        self.full_chat_list = self.get_full_chat_list()

    def get_full_user_list(self):
        self.mycursor.execute("SELECT DISTINCT user_id FROM users WHERE name IS NULL")
        return list(map(lambda x: int(x[0]), self.mycursor.fetchall()))

    def get_user_chat_list(self, user_id):
        self.mycursor.execute("SELECT chat_id FROM users WHERE user_id = %s", (user_id,))
        return list(map(lambda x: int(x[0]), self.mycursor.fetchall()))

    def chat_info(self, chat_id, start=None, end=None):
        append_sql = ''
        val = (chat_id,)

        if start:
            append_sql += " AND creation_date >= %s"
            val = val + (start,)

        self.mycursor.execute("SELECT creation_date FROM messages "
                              "WHERE chat_id = %s ORDER BY creation_date LIMIT 1;",
                              (chat_id,))
        rec = self.mycursor.fetchone()
        if rec and (not start or rec[0] > start):
            start = rec[0]

        if end:
            append_sql += " AND creation_date <= %s"
            val = val + (end,)
        self.mycursor.execute("SELECT creation_date FROM messages "
                              "WHERE chat_id = %s ORDER BY creation_date DESC LIMIT 1;",
                              (chat_id,))
        rec = self.mycursor.fetchone()
        if rec and (not end or rec[0] < end):
            end = rec[0]

        self.mycursor.execute("SELECT COUNT(*) FROM messages WHERE chat_id = %s" + append_sql + ';', val)
        messages = self.mycursor.fetchone()[0]
        self.mycursor.execute("SELECT COUNT(*) FROM words "
                              "JOIN messages ON messages.id = message_id "
                              "WHERE chat_id = %s" + append_sql + ';', val)
        words = self.mycursor.fetchone()[0]
        self.mycursor.execute("SELECT COUNT(*) FROM emoticons "
                              "JOIN messages ON messages.id = message_id "
                              "WHERE chat_id = %s" + append_sql + ';', val)
        emoticons = self.mycursor.fetchone()[0]
        return messages, words, emoticons, start, end

    def text_for_cloud(self, chat_id, start=None, end=None):
        sql = "SELECT normal_form FROM words JOIN messages ON messages.id = message_id WHERE chat_id = %s"
        val = (chat_id,)
        if start:
            sql += " AND creation_date >= %s"
            val = val + (start,)
        if end:
            sql += " AND creation_date <= %s"
            val = val + (end,)
        self.mycursor.execute(sql + ';', val)
        words = self.mycursor.fetchall()

        text = ''
        for i in words:
            text += ' ' + i[0]
        return text

    def most_commonly_used_emoticons(self, chat_id, start=None, end=None):
        sql = "SELECT emoticon, COUNT(*) FROM emoticons JOIN messages ON messages.id = message_id " \
              "WHERE chat_id = %s"
        val = (chat_id,)
        if start:
            sql += " AND creation_date >= %s"
            val = val + (start,)
        if end:
            sql += " AND creation_date <= %s"
            val = val + (end,)
        self.mycursor.execute(sql + ' GROUP BY emoticon ORDER BY COUNT(*) DESC;', val)
        emoticons = self.mycursor.fetchall()
        return emoticons


db = MySQL()

if __name__ == '__main__':
    # ret = db.handle_new_messages()
    # print(f'Обработано сообщений {str(ret[0])}\n'
    #       f'Добавлено слов {str(ret[1])}\n'
    #       f'Добавлено эмодзи {str(ret[2])}')
    print(db.get_full_user_list())
