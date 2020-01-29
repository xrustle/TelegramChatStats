from bot.config import API, MTPROTO, CHATS
from telethon import TelegramClient, connection
import logging
from bot.db import db

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

client = TelegramClient(
            'session-telegram',
            **API,
            connection=connection.ConnectionTcpMTProxyRandomizedIntermediate,
            proxy=tuple(MTPROTO))


def collect_messages():
    """
    Используется для сбора всех новых сообщений из списка чатов указанных в конфиге
    """
    async def run():
        async for dialog in client.iter_dialogs():
            if dialog.id in CHATS:
                print('Собираем данные диалога', dialog.name)
                async for message in client.iter_messages(dialog):
                    if not db.insert_message(dialog.id, message.to_dict()):
                        break
                members = await client.get_participants(dialog)
                for member in members:
                    db.insert_message(dialog.id, member.to_dict(), 'Members')
    with client:
        client.loop.run_until_complete(run())


def show_dialogs():
    async def run():
        async for dialog in client.iter_dialogs():
            print('{:<15} {}'.format(dialog.id, dialog.name))
    with client:
        client.loop.run_until_complete(run())


if __name__ == '__main__':
    show_dialogs()
