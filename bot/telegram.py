import bot.config as config
from bot.db import db
import telebot


telebot.apihelper.proxy = config.PROXY
bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=['start'])
def command_start(m):
    cid = m.chat.id
    if cid != my_id:
        return 0
    bot.send_message(cid, get('ru', 'start'))


@bot.message_handler(content_types=["text"])
def print_message(m: telebot.types.Message):
    db.insert(m.json)


if __name__ == "__main__":
    my_id = config.ID
    bot.polling()
