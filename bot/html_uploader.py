from lxml import html
from datetime import datetime
from bot.db import db
import re
import os


def parse_html(user_id: int, file: bytes):
    text = html.fromstring(file)
    chat_name = text.xpath("//div[@class='page_header']//div[@class='text bold']/text()")
    chat_name = re.sub(r'\r?\n', ' ', chat_name[0]).strip(' ')

    messages = text.xpath("//div[contains(@class, 'message default clearfix') or "
                          "contains(@class, 'message default clearfix joined')]")

    last_from_name = ''
    number_of_new_messages = 0
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
        for text_part in message.xpath(".//div[@class='text']")[0].itertext():
            text += text_part
        text = re.sub(r'\r?\n', ' ', text).strip(' ')

        if text:
            if not db.insert_message('Chat'+str(user_id)+chat_name,
                                     {'_id': msg_id,
                                      'date': date,
                                      'message': text,
                                      'from_id': from_name}):
                break
            else:
                number_of_new_messages += 1

    ret_dict = {'name': chat_name,
                'count': number_of_new_messages}
    return ret_dict


if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(path, 'messages.html'), 'rb') as chat_file:
        data = chat_file.read()
        print(parse_html(1234, data))
