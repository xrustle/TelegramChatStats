import bot.config as config
import telebot
from telebot import types
from bot.db_mysql import db
from datetime import datetime
from bot.wcloud import generate_cloud_image
from bot.html_uploader import parse_html
import logging
from threading import Thread, Lock
import traceback
import time
import re
import os

lock = Lock()

path = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=os.path.join(path, 'bot.log'),
                    filemode='w',
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
word_stats = {}


def log_user_activity(action, msg: types.Message):
    try:
        if not msg.json['from']['is_bot']:
            text = re.sub(r"[^\x00-\x7F]", " ", str(msg.json))
            if msg.from_user.id not in db.full_user_list:
                logging.info(f'UNKNOWN USER. {action}. {text}')
            else:
                logging.info(f'{action}. {text}')
    except Exception as e:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
        bot.send_message(msg.chat.id, e)


def get_selected_chat(m: types.Message):
    if m.chat.type == 'group':
        return m.chat.id
    elif m.chat.id in users:
        return users[m.chat.id]
    else:
        return None


@bot.message_handler(commands=['start'])
def show_help(m: types.Message):
    log_user_activity('/help', m)
    if m.from_user.id not in db.full_user_list:
        return
    bot.send_message(m.chat.id, '/help - вызвать данную инструкцию.\n'
                                '/chat - выбрать чат для статистики.\n'
                                '/interval - выбрать временной интервал, по которому будет отображаться статистика.\n'
                                '/stats - нажмите для получения статистики по выбранному чату и диапазону дат.')


@bot.message_handler(commands=['help'])
def help_command(m: types.Message):
    show_help(m)


@bot.message_handler(commands=['chat'])
def select_chat(m: types.Message):
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
                markup.row(types.InlineKeyboardButton(text=str(db.full_chat_list[chat_id]),
                                                      callback_data='Switch_chat ' + str(chat_id)))
            bot.send_message(m.chat.id, 'Выберите чатик:', reply_markup=markup)
    except Exception as e:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
        bot.send_message(m.chat.id, e)


@bot.message_handler(commands=['interval'])
def select_interval(m: types.Message):
    log_user_activity('/interval', m)
    if m.from_user.id not in db.full_user_list:
        return

    selected_chat = get_selected_chat(m)
    if not selected_chat:
        bot.send_message(m.chat.id, 'Чтобы выбирать интервал, сначала нужно выбрать чат')
        select_chat(m)
        return

    try:
        markup = types.InlineKeyboardMarkup()
        start = db.year_stamp(selected_chat)
        end = db.year_stamp(selected_chat, end=True)
        if start != end:
            for i in range(start, end + 1):
                markup.row(types.InlineKeyboardButton(text=str(i) + ' год', callback_data='Switch_interval ' + str(i)))
        markup.row(types.InlineKeyboardButton(text='За все время', callback_data='Switch_interval all'))
        markup.row(types.InlineKeyboardButton(text='Задать вручную', callback_data='Switch_interval manual'))
        bot.send_message(m.chat.id, 'Выберите интервал:', reply_markup=markup)
    except Exception as e:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
        bot.send_message(m.chat.id, e)


@bot.message_handler(commands=['stats'])
def stats_command(m: types.Message):
    log_user_activity('/stats', m)
    if m.from_user.id not in db.full_user_list:
        return

    selected_chat = get_selected_chat(m)
    if not selected_chat:
        bot.send_message(m.chat.id, 'Чтобы получить статистику, нужно выбрать чат')
        select_chat(m)
        return

    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton(text='Облако слов', callback_data='Stats wcloud'))
        markup.row(types.InlineKeyboardButton(text='Самые частые эмодзи', callback_data='Stats emoji'))
        markup.row(types.InlineKeyboardButton(text='Статистика по слову', callback_data='Stats word'))
        bot.send_message(m.chat.id, 'На сегодня могу предложить следующее:', reply_markup=markup)
    except Exception as e:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
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
        bot.reply_to(m, f'{info["title"]}'
                        f'Текстовых сообщений *{info["count"]}*'
                        f'Сохранено сообщений *{info["handled"][0]}*'
                        f'Слов *{info["handled"][1]}*'
                        f'Эмодзи *{info["handled"][2]}*', parse_mode='markdown')
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
            traceback_error_string = traceback.format_exc()
            logging.error(traceback_error_string)
            bot.send_message(m.chat.id, e)


def current_chat_info(chat_id, start, end):
    info = db.chat_info(chat_id, start, end)
    text = f'*{db.full_chat_list[chat_id]}*\n' \
           f'`Интервал  `{info[3].strftime("%d.%m.%y")} - {info[4].strftime("%d.%m.%y")}\n' \
           f'`Сообщений `{str(info[0])}\n' \
           f'`Слов      `{str(info[1])}\n' \
           f'`Эмодзи    `{str(info[2])}'
    return text


def send_word_cloud(selected_chat, start, end, chat_id):
    with lock:
        text = db.text_for_cloud(selected_chat, start=start, end=end)
        bot.send_photo(chat_id, generate_cloud_image(text))


def wcloud(m: types.Message, selected_chat):
    log_user_activity('WCLOUD', m)

    try:
        bot.edit_message_text(chat_id=m.chat.id,
                              message_id=m.message_id,
                              text='Создаем облако...',
                              parse_mode='markdown')
        start = None
        end = None
        if m.chat.id in starts:
            start = starts[m.chat.id]
        if m.chat.id in ends:
            end = ends[m.chat.id]
        send_word_cloud(selected_chat, start, end, m.chat.id)
    except Exception as e:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
        bot.send_message(m.chat.id, e)


def emoji(m: types.Message, selected_chat):
    log_user_activity('EMOJI', m)
    try:
        bot.edit_message_text(chat_id=m.chat.id,
                              message_id=m.message_id,
                              text='Строим статистику...',
                              parse_mode='markdown')
        start = None
        end = None
        if m.chat.id in starts:
            start = starts[m.chat.id]
        if m.chat.id in ends:
            end = ends[m.chat.id]
        emoticons = db.most_commonly_used_emoticons(selected_chat, start, end)
        text = ''
        num = 0
        limit = 30
        for emoji in emoticons:
            num += 1
            if num > limit:
                break
            text += f'`{emoji[0]} {str(emoji[1])} `'

        bot.edit_message_text(chat_id=m.chat.id,
                              message_id=m.message_id,
                              text=text,
                              parse_mode='markdown')
    except Exception as e:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
        bot.send_message(m.chat.id, e)


@bot.callback_query_handler(func=lambda query: True)
def chat_select_callback(query: types.CallbackQuery):
    try:
        callback = query.data
        m = query.message
        log_user_activity('CALLBACK', m)
        if callback.startswith('Switch_chat'):
            bot.answer_callback_query(query.id)
            new_chat_id = int(callback[12:])
            if new_chat_id in db.get_user_chat_list(m.chat.id):
                text = current_chat_info(new_chat_id, starts.get(m.chat.id), ends.get(m.chat.id))
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
            selected_chat = get_selected_chat(m)
            if new_interval == 'manual':
                manuals[m.chat.id] = 1
                bot.edit_message_text(chat_id=m.chat.id,
                                      message_id=m.message_id,
                                      text='Отправьте сообщение с интервалом в формате\n*dd/mm/yy-dd/mm/yy*:',
                                      parse_mode='markdown')
            elif new_interval == 'all':
                log_user_activity('INTERVAL CHANGED', m)
                if m.chat.id in starts:
                    del starts[m.chat.id]
                if m.chat.id in ends:
                    del ends[m.chat.id]
                text = current_chat_info(selected_chat, starts.get(m.chat.id), ends.get(m.chat.id))
                bot.edit_message_text(chat_id=m.chat.id,
                                      message_id=m.message_id,
                                      text=text,
                                      parse_mode='markdown')
            else:
                log_user_activity('INTERVAL CHANGED', m)
                starts[m.chat.id] = datetime.strptime('01/01/' + new_interval, '%d/%m/%Y')
                ends[m.chat.id] = datetime.strptime('31/12/' + new_interval, '%d/%m/%Y')
                text = current_chat_info(selected_chat, starts.get(m.chat.id), ends.get(m.chat.id))
                bot.edit_message_text(chat_id=m.chat.id,
                                      message_id=m.message_id,
                                      text=text,
                                      parse_mode='markdown')
        elif callback.startswith('Stats'):
            bot.answer_callback_query(query.id)
            stats_type = callback[6:]
            selected_chat = get_selected_chat(m)
            if stats_type == 'wcloud':
                wcloud(m, selected_chat)
            elif stats_type == 'emoji':
                emoji(m, selected_chat)
            elif stats_type == 'word':
                word_stats[m.chat.id] = 1
                bot.edit_message_text(chat_id=m.chat.id,
                                      message_id=m.message_id,
                                      text='Введите русское слово')

    except Exception as e:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
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

                selected_chat = get_selected_chat(m)
                text = current_chat_info(selected_chat, starts.get(m.chat.id), ends.get(m.chat.id))
                bot.send_message(chat_id=m.chat.id, text=text, parse_mode='markdown')
            except ValueError:
                bot.send_message(m.chat.id, 'Попробуйте ещё раз...\nФормат *dd/mm/yy-dd/mm/yy*', parse_mode='markdown')
    except Exception as e:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
        bot.send_message(m.chat.id, e)


@bot.message_handler(func=lambda m: m.chat.id in word_stats)
def set_manual_interval(m: types.Message):
    try:
        log_user_activity('WORD_STATS', m)
        if m.text:
            word = m.text

            start = None
            end = None
            if m.chat.id in starts:
                start = starts[m.chat.id]
            if m.chat.id in ends:
                end = ends[m.chat.id]

            selected_chat = get_selected_chat(m)
            del word_stats[m.chat.id]
            stats = db.word_stats(selected_chat, word, start, end)
            if stats:
                user_stats = {}
                uname_len = 0
                text = ''
                for user in stats:
                    user_name = str(user[0])
                    if user[2]:
                        user_name = user[2]
                    elif not user[3] and not user[4] and not user[5] and user[1]:
                        user_name = user[1]
                    else:
                        if user[3] and user[4]:
                            user_name = user[3] + ' ' + user[4]
                        elif user[3]:
                            user_name = user[3]
                        elif user[4]:
                            user_name = user[4]
                        elif user[5]:
                            user_name = user[4]
                    user_stats[user_name] = str(user[6])
                    if len(user_name) > uname_len:
                        uname_len = len(user_name)

                for user in user_stats:
                    text += f'`{user:<{uname_len}} {user_stats[user]}`\n'
                bot.send_message(chat_id=m.chat.id, text=text, parse_mode='markdown')
            else:
                bot.send_message(chat_id=m.chat.id,
                                 text='Такого слова не найдено в выбранном чате на выбранном интервале')
    except Exception as e:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
        bot.send_message(m.chat.id, e)


def telegram_polling():
    try:
        logging.info('Bot started...')
        bot.polling(none_stop=True, timeout=60)
    except Exception:
        traceback_error_string = traceback.format_exc()
        logging.error(traceback_error_string)
        bot.stop_polling()
        time.sleep(120)
        telegram_polling()


if __name__ == "__main__":
    logging.info('Bot started...')
    telegram_polling()
