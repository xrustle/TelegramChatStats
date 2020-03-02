import mysql.connector
from bot.config import MYSQL

DB_NAME = 'telegram'

mydb = mysql.connector.connect(
    host=MYSQL['host'],
    user=MYSQL['user'],
    password=MYSQL['password']
    # auth_plugin='mysql_native_password'
)

mycursor = mydb.cursor()
mycursor.execute(f'CREATE DATABASE if NOT EXISTS {DB_NAME}')

mydb = mysql.connector.connect(**MYSQL)
mycursor = mydb.cursor()

query = \
    "CREATE TABLE IF NOT EXISTS emoticons (" \
    "  id int(10) unsigned NOT NULL AUTO_INCREMENT," \
    "  chat_id int(10) unsigned NOT NULL," \
    "  emoticon varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL," \
    "  PRIMARY KEY (id)" \
    ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"

mycursor.execute(query)

emo = u'\U0001F4E5'
chat_id = 123
sql = f"INSERT INTO emoticons (chat_id, emoticon) VALUES (%s, %s);"
val = (str(chat_id), emo)
mycursor.execute(sql, val)
mydb.commit()
