import bot.config as config
import telebot
from telebot import types
from bot.db_select import db
from datetime import datetime
from bot.wcloud import generate_cloud_image
from bot.html_uploader import parse_html
import logging
from threading import Thread, Lock
import re
import os

lock = Lock()

path = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=os.path.join(path, 'bot.log'),
                    filemode='a',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')

if config.PROXY_ON:
    telebot.apihelper.proxy = config.PROXY

bot = telebot.TeleBot(config.TOKEN)

users = {}
starts = {}
ends = {}
manuals = {}


def log_user_activity(action, msg: types.Message):
    try:
        if not msg.json['from']['is_bot']:
            text = re.sub(r"[^\x00-\x7F]", " ", str(msg.json))
            if msg.from_user.id not in db.full_user_list:
                logging.info(f'UNKNOWN USER. {action}. {text}')
            else:
                logging.info(f'{action}. {text}')
    except Exception as e:
        bot.send_message(msg.chat.id, 'Error in action: ' + action)
        bot.send_message(msg.chat.id, e)


def get_selected_chat(m: types.Message):
    if m.chat.type == 'group':
        return m.chat.id
    elif m.chat.id in users:
        return users[m.chat.id]
    else:
        return None


@bot.message_handler(commands=['start'])
def start_command(m: types.Message):
    log_user_activity('/start', m)
    if m.from_user.id not in db.full_user_list:
        return

    try:
        if m.chat.type == 'group':
            bot.send_message(m.chat.id, 'В группе нельзя выбирать чат. Статистика возможна только по этой группе.')
        else:
            chat_list = db.get_user_chat_list(m.chat.id)
            markup = types.InlineKeyboardMarkup()
            for chat_id in chat_list:
                markup.row(types.InlineKeyboardButton(text=str(chat_list[chat_id]),
                                                      callback_data='Switch_chat ' + str(chat_id)))
            bot.send_message(m.chat.id, 'Выберите чатик:', reply_markup=markup)
    except Exception as e:
        bot.send_message(m.chat.id, e)


@bot.message_handler(commands=['help'])
def show_help(m: types.Message):
    log_user_activity('/help', m)
    if m.from_user.id not in db.full_user_list:
        return
    bot.send_message(m.chat.id, '/start - начать пользоваться ботом. '
                                'Позволяет выбрать чат для статистики при личном общении с ботом.\n'
                                '/interval - выбрать временной интервал, по которому будет отображаться статистика.\n'
                                '/stats - запросить статистику. Бот предложит несколько вариантов.')


@bot.message_handler(commands=['interval'])
def select_interval(m: types.Message):
    log_user_activity('/interval', m)
    if m.from_user.id not in db.full_user_list:
        return

    try:
        markup = types.InlineKeyboardMarkup()
        year = datetime.now().year
        for i in range(year - 4, year + 1):
            markup.row(types.InlineKeyboardButton(text=str(i) + ' год', callback_data='Switch_interval ' + str(i)))
        markup.row(types.InlineKeyboardButton(text='За все время', callback_data='Switch_interval all'))
        markup.row(types.InlineKeyboardButton(text='Задать вручную', callback_data='Switch_interval manual'))
        bot.send_message(m.chat.id, 'Выберите интервал:', reply_markup=markup)
    except Exception as e:
        bot.send_message(m.chat.id, e)


def send_word_cloud(selected_chat, start, end, chat_id):
    with lock:
        text = db.text_for_cloud(selected_chat, start=start, end=end)
        bot.send_photo(chat_id, generate_cloud_image(text))


@bot.message_handler(commands=['stats'])
def stats_command(m: types.Message):
    log_user_activity('/stats', m)
    if m.from_user.id not in db.full_user_list:
        return

    selected_chat = get_selected_chat(m)
    if not selected_chat:
        start_command(m)
        return

    try:
        info = str(db.full_chat_list[selected_chat])
        start = None
        end = None
        if m.chat.id in starts:
            start = starts[m.chat.id]
            info += '\nC ' + str(start)
        if m.chat.id in ends:
            end = ends[m.chat.id]
            info += '\nПо ' + str(end)

        bot.send_message(m.chat.id, info)
        bot.send_message(m.chat.id, text='Лоадинг...')

        send_word_cloud(selected_chat, start, end, m.chat.id)
    except Exception as e:
        bot.send_message(m.chat.id, e)


@bot.message_handler(commands=['emoji'])
def emoji_command(m: types.Message):
    log_user_activity('/emoji', m)
    if m.from_user.id not in db.full_user_list:
        return

    selected_chat = get_selected_chat(m)
    if not selected_chat:
        start_command(m)
        return

    try:
        emoticons = db.most_commonly_used_emoticons(selected_chat)
        text = ''
        num = 0
        limit = 30
        for emoji in emoticons:
            num += 1
            if num > limit:
                break
            text += f'{emoji["emoticon"]}{str(emoji["count"])}\t'

        bot.send_message(m.chat.id, text=text)
    except Exception as e:
        bot.send_message(m.chat.id, e)


def parse_html_file(html_file, m: types.Message):
    with lock:
        logging.info('SYSTEM start upload file ' + html_file.file_path)
        downloaded_file = bot.download_file(html_file.file_path)
        # if not os.path.exists(os.path.join(path, 'uploaded')):
        #     os.makedirs(os.path.join(path, 'uploaded'))
        # with open(os.path.join(path, 'uploaded', html_file.file_id + '.html'), 'wb') as file:
        #     file.write(downloaded_file)
        info = parse_html(m.from_user.id, downloaded_file)
        db.update_full_chat_list()
        bot.reply_to(m, f'Загружено *{info["count"]}* новых сообщений чатика *{info["title"]}*', parse_mode='markdown')
        logging.info('SYSTEM uploaded file ' + html_file.file_path)


@bot.message_handler(content_types=['document'])
def upload_html(m: types.Message):
    if m.document.mime_type == 'text/html':
        log_user_activity('UPLOAD HTML', m)
        if m.from_user.id not in db.full_user_list:
            return
        try:
            html_file = bot.get_file(m.document.file_id)
            Thread(target=parse_html_file, args=(html_file, m)).start()
            bot.reply_to(m, f'Загружаем чатик. Обрабатываем в фоновом режиме...')
        except Exception as e:
            bot.send_message(m.chat.id, e)


@bot.callback_query_handler(func=lambda query: True)
def chat_select_callback(query: types.CallbackQuery):
    try:
        callback = query.data
        m = query.message
        log_user_activity('CALLBACK', m)
        if callback.startswith('Switch_chat'):
            bot.answer_callback_query(query.id)
            new_chat_id = callback[12:]
            old_selected_chat = users.get(query.from_user.id)
            print(new_chat_id)
            print(db.get_user_chat_list(m.chat.id))
            if old_selected_chat and old_selected_chat == new_chat_id:
                text = 'Вы уже выбрали чат *' + db.full_chat_list[new_chat_id] + '*'
            elif new_chat_id in db.get_user_chat_list(m.chat.id):
                text = 'Вы выбрали чат *' + db.full_chat_list[new_chat_id] + '*'
                users[query.from_user.id] = new_chat_id
            else:
                text = 'Этот чат чот больше не доступен. Попробуйте выбрать снова: /start'

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
    except Exception as e:
        bot.send_message(query.message.chat.id, e)


@bot.message_handler(func=lambda m: m.chat.id in manuals)
def set_manual_interval(m: types.Message):
    try:
        log_user_activity('INTERVAL CHANGED', m)
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
    except Exception as e:
        bot.send_message(m.chat.id, e)


if __name__ == "__main__":
    my_id = config.ID
    logging.info('Bot started...')
    bot.polling()
