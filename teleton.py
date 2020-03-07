from bot.config import API, CHATS, ID
from telethon import TelegramClient
import logging
from bot.db_mysql import db


logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

client = TelegramClient('session-telegram', **API)


def collect_messages():
    """
    Используется для сбора всех новых сообщений из списка чатов указанных в конфиге
    """
    async def run():
        async for dialog in client.iter_dialogs():
            if dialog.id in CHATS:
                print('Собираем данные диалога: ', dialog.name)
                chat_id = db.insert_chat(str(dialog.id), u'\U0001F465' + ' ' + dialog.name)

                members = await client.get_participants(dialog)
                users = {}
                for member in members:
                    if not member.bot:
                        users[member.id] = db.insert_user(chat_id,
                                                          str(member.id),
                                                          member.first_name,
                                                          member.last_name,
                                                          member.username)
                users[ID] = db.insert_user(chat_id, str(ID), 'Dmitry', 'Batorov')

                number_of_new_messages = 0
                async for m in client.iter_messages(dialog):
                    if m.text and not m.sender.bot and not m.text.startswith('**Top Players**'):
                        if m.sender_id not in users:
                            users[m.sender_id] = db.insert_user(chat_id, str(m.sender_id))
                        if not db.insert_message(chat_id, str(m.id), m.date, m.text, users[m.sender_id]):
                            break
                        else:
                            number_of_new_messages += 1
                print(f'\tНовых сообщений собрано: {number_of_new_messages}')
    with client:
        client.loop.run_until_complete(run())


def show_dialogs():
    async def run():
        async for dialog in client.iter_dialogs():
            print('{:<15} {}'.format(dialog.id, dialog.name))
    with client:
        client.loop.run_until_complete(run())


if __name__ == '__main__':
    collect_messages()  # Собираем историю сообщений
    ret = db.handle_new_messages()  # Обрабатываем собранные сообщения
    print(
        f'Обработано сообщений {str(ret[0])}\n'
        f'Добавлено слов {str(ret[1])}\n'
        f'Добавлено эмодзи {str(ret[2])}'
    )
    # show_dialogs()
