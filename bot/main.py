import bot.config as config
from bot.db import db
from bot.teleton import collect_messages
import telebot

if config.PROXY_ON:
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
    collect_messages()  # Собираем историю сообщений
    db.handle_new_messages()  # Обрабатываем собранные сообщения
    my_id = config.ID
    print('Запуск бота...')
    # bot.polling()  # Запускаем бота статиста
