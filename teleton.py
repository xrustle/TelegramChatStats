from bot.config import API, CHATS
from telethon import TelegramClient
import logging
from bot.db import db


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
                number_of_new_messages = 0
                number_of_new_members = 0
                async for m in client.iter_messages(dialog):
                    if m.text and not m.sender.bot and not m.text.startswith('**Top Players**'):
                        if not db.insert_message(dialog.id, {'_id': m.id,
                                                             'date': m.date,
                                                             'message': m.text,
                                                             'from_id': m.sender_id}):
                            break
                        else:
                            number_of_new_messages += 1
                members = await client.get_participants(dialog)
                users = []
                for member in members:
                    if not member.bot:
                        user = {'id': member.id,
                                'first_name': member.first_name,
                                'last_name': member.last_name,
                                'username': member.username}
                        users.append(user)
                db.insert_members(dialog.id, {'title': u'\U0001F465' + ' ' + dialog.name, 'users': users})
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
    db.handle_new_messages()  # Обрабатываем собранные сообщения
    # show_dialogs()
