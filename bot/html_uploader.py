from lxml import html
from bot.config import ID
from datetime import datetime
from bot.db_mysql import db
import os
import re


def parse_html(user_id: int, file: bytes):
    text = html.fromstring(file)
    chat_name = text.xpath("//div[@class='page_header']//div[@class='text bold']/text()")
    chat_name = re.sub(r'\r?\n', ' ', chat_name[0]).strip(' ')
    chat_id = db.insert_chat(str(user_id) + ' ' + chat_name, u'\U0001F4E5' + ' ' + chat_name)

    messages = text.xpath("//div[contains(@class, 'message default clearfix') or "
                          "contains(@class, 'message default clearfix joined')]")

    last_from_name = ''
    users = {}
    number_of_new_messages = 0

    db.insert_user(chat_id, ID)
    db.insert_user(chat_id, user_id)

    for message in messages:
        msg_id = message.xpath('./@id')[0]
        date = message.xpath(".//div[contains(@class, 'date')]/@title")[0]
        date = datetime.strptime(date, '%d.%m.%Y %H:%M:%S')

        from_name = message.xpath(".//div[@class='from_name']/text()")
        if from_name:
            from_name = re.sub(r'\r?\n', ' ', from_name[0]).strip(' ')
            last_from_name = from_name
        else:
            from_name = last_from_name

        text = ''
        xpath_text = message.xpath(".//div[@class='text']")
        if xpath_text:
            for text_part in xpath_text[0].itertext():
                text += text_part
        text = re.sub(r'\r?\n', ' ', text).strip(' ')

        if from_name not in users:
            users[from_name] = db.insert_user(chat_id, from_name, name=from_name)

        if text:
            if not db.insert_message(chat_id, msg_id, date, text, users[from_name]):
                break
            else:
                number_of_new_messages += 1

    ret = db.handle_new_messages()

    return {'count': number_of_new_messages,
            'handled': ret,
            'title': u'\U0001F4E5' + ' ' + chat_name}


if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(path, 'messages.html'), 'rb') as chat_file:
        data = chat_file.read()
        print(parse_html(1234, data))
    # db.handle_new_messages()
