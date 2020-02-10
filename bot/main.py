import bot.config as config
import telebot
from telebot import types
from bot.db_select import db
from datetime import datetime

if config.PROXY_ON:
    telebot.apihelper.proxy = config.PROXY

bot = telebot.TeleBot(config.TOKEN)

full_user_list = db.full_user_list()
chat_titles = db.get_full_chat_list()

users = {}
starts = {}
ends = {}
manuals = {}


def get_selected_chat(m: types.Message):
    if m.chat.type == 'group':
        return m.chat.id
    elif m.chat.id in users:
        return users[m.chat.id]
    else:
        return None


@bot.message_handler(commands=['start'])
def start_command(m: types.Message):
    if m.from_user.id not in full_user_list:
        return

    if m.chat.type == 'group':
        bot.send_message(m.chat.id, 'В группе нельзя выбирать чат. Статистика возможна только по этой группе.')
    else:
        chat_list = db.get_user_chat_list(m.chat.id)
        markup = types.InlineKeyboardMarkup()
        for chat_id in chat_list:
            markup.row(types.InlineKeyboardButton(text=str(chat_list[chat_id]),
                                                  callback_data='Switch_chat ' + str(chat_id)))
        bot.send_message(m.chat.id, 'Выберите чатик:', reply_markup=markup)


@bot.message_handler(commands=['help'])
def show_help(m: types.Message):
    if m.from_user.id not in full_user_list:
        return
    bot.send_message(m.chat.id, '/start - начать пользоваться ботом. '
                                'Позволяет выбрать чат для статистики при личном общении с ботом.\n'
                                '/interval - выбрать временной интервал, по которому будет отображаться статистика.\n'
                                '/stats - запросить статистику. Бот предложит несколько вариантов.')


@bot.message_handler(commands=['interval'])
def select_interval(m: types.Message):
    if m.from_user.id not in full_user_list:
        return
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton(text='2018 год', callback_data='Switch_interval 2018'))
    markup.row(types.InlineKeyboardButton(text='2019 год', callback_data='Switch_interval 2019'))
    markup.row(types.InlineKeyboardButton(text='За все время', callback_data='Switch_interval all'))
    markup.row(types.InlineKeyboardButton(text='Задать вручную', callback_data='Switch_interval manual'))
    bot.send_message(m.chat.id, 'Выберите интервал:', reply_markup=markup)


@bot.message_handler(commands=['stats'])
def command_start(m: types.Message):
    if m.from_user.id not in full_user_list:
        return

    selected_chat = get_selected_chat(m)
    if not selected_chat:
        start_command(m)
        return

    info = 'chat = ' + str(chat_titles[selected_chat])
    if m.chat.id in starts:
        start = starts[m.chat.id]
        info += ', start = ' + str(start)
    if m.chat.id in ends:
        end = ends[m.chat.id]
        info += ', end = ' + str(end)

    bot.send_message(m.chat.id, info)


@bot.callback_query_handler(func=lambda query: True)
def chat_select_callback(query: types.CallbackQuery):
    callback = query.data
    m = query.message
    if callback.startswith('Switch_chat'):
        bot.answer_callback_query(query.id)
        # bot.send_chat_action(m.chat.id, 'typing')
        new_chat_id = int(callback[12:])
        old_selected_chat = users.get(query.from_user.id)
        if old_selected_chat and old_selected_chat == new_chat_id:
            text = 'Вы уже выбрали чат *' + chat_titles[new_chat_id] + '*'
        else:
            text = 'Вы выбрали чат *' + chat_titles[new_chat_id] + '*'
        users[query.from_user.id] = new_chat_id
        bot.edit_message_text(chat_id=m.chat.id,
                              message_id=m.message_id,
                              text=text,
                              parse_mode='markdown')
    elif callback.startswith('Switch_interval'):
        bot.answer_callback_query(query.id)
        new_interval = callback[16:]
        if new_interval == 'manual':
            manuals[m.chat.id] = 1
            bot.edit_message_text(chat_id=m.chat.id,
                                  message_id=m.message_id,
                                  text='Отправьте сообщение с интервалом в формате\n*dd/mm/yy-dd/mm/yy*:',
                                  parse_mode='markdown')
        elif new_interval == 'all':
            if m.chat.id in starts:
                del starts[m.chat.id]
            if m.chat.id in ends:
                del ends[m.chat.id]
            bot.edit_message_text(chat_id=m.chat.id,
                                  message_id=m.message_id,
                                  text='Фильтр на даты сняты')
        else:
            starts[m.chat.id] = datetime.strptime('01/01/' + new_interval, '%d/%m/%Y')
            ends[m.chat.id] = datetime.strptime('31/12/' + new_interval, '%d/%m/%Y')
            bot.edit_message_text(chat_id=m.chat.id,
                                  message_id=m.message_id,
                                  text='Ура! Статистика за ' + new_interval + ' год!')


@bot.message_handler(func=lambda m: m.chat.id in manuals)
def set_manual_interval(m: types.Message):
    if m.text:
        try:
            start = datetime.strptime(m.text[:8], '%d/%m/%y')
            end = datetime.strptime(m.text[9:18], '%d/%m/%y')
            del manuals[m.chat.id]
            starts[m.chat.id] = start
            ends[m.chat.id] = end
            bot.send_message(m.chat.id, 'Новый интервал установлен!\n*' + m.text[:18] + '*', parse_mode='markdown')
        except ValueError:
            bot.send_message(m.chat.id, 'Попробуйте ещё раз...\nФормат *dd/mm/yy-dd/mm/yy*', parse_mode='markdown')


if __name__ == "__main__":
    my_id = config.ID
    print('Запуск бота...')
    bot.polling()
