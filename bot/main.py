import bot.config as config
import telebot
from telebot import types
from bot.db_select import db

if config.PROXY_ON:
    telebot.apihelper.proxy = config.PROXY

bot = telebot.TeleBot(config.TOKEN)

full_user_list = db.full_user_list()
chat_titles = db.get_full_chat_list()
users = {}


def get_selected_chat(m: types.Message):
    if m.chat.type == 'group':
        return m.chat.id
    elif m.chat.id in users:
        return users[m.chat.id]
    else:
        return None


@bot.message_handler(commands=['start'])
def select_chat(m: types.Message):
    if m.from_user.id not in full_user_list:
        return

    if m.chat.type == 'group':
        bot.send_message(m.chat.id, 'В группе нельзя выбирать чат. Статистика возможна только по этой группе.')
    else:
        chat_list = db.get_user_chat_list(m.chat.id)
        markup = types.InlineKeyboardMarkup()
        for chat_id in chat_list:
            markup.row(types.InlineKeyboardButton(text=str(chat_list[chat_id]), callback_data='Switch_chat ' + str(chat_id)))
        bot.send_message(m.chat.id, 'Выберите чатик:', reply_markup=markup)


@bot.message_handler(commands=['help'])
def select_chat(m: types.Message):
    if m.from_user.id not in full_user_list:
        return
    bot.send_message(m.chat.id, '/start - начать пользоваться ботом. '
                                'Позволяет выбрать чат для статистики при личном общении с ботом.\n'
                                '/interval - выбрать временной интервал, по которому будет отображаться статистика.\n'
                                '/stats - запросить статистику. Бот предложит несколько вариантов.')


@bot.callback_query_handler(func=lambda query: True)
def chat_select_callback(query: types.CallbackQuery):
    callback = query.data
    m = query.message
    if callback.startswith('Switch_chat '):
        chat_list = db.get_user_chat_list(m.chat.id)
        bot.answer_callback_query(query.id)
        # bot.send_chat_action(m.chat.id, 'typing')
        new_chat_id = int(callback[12:])
        old_selected_chat = users.get(query.from_user.id)
        if old_selected_chat and old_selected_chat == new_chat_id:
            text = 'Вы уже выбрали чат *' + chat_list[new_chat_id] + '*'
        else:
            text = 'Вы выбрали чат *' + chat_list[new_chat_id] + '*'
        users[query.from_user.id] = new_chat_id
        bot.edit_message_text(chat_id=m.chat.id,
                              message_id=m.message_id,
                              text=text,
                              parse_mode='markdown')


@bot.message_handler(commands=['start'])
def command_start(m: types.Message):
    if m.from_user.id not in full_user_list:
        return

    selected_chat = get_selected_chat(m)
    if not selected_chat:
        select_chat(m)
        return

    bot.send_message(m.chat.id, m.text)


@bot.message_handler(content_types=['text'])
def command_start(m: types.Message):
    if m.from_user.id not in full_user_list:
        return

    selected_chat = get_selected_chat(m)
    if not selected_chat:
        select_chat(m)
        return

    bot.send_message(m.chat.id, str(selected_chat))


if __name__ == "__main__":
    my_id = config.ID
    print('Запуск бота...')
    bot.polling()
