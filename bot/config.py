import json
import os

path = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(path, 'config.json'), encoding='utf-8') as json_data_file:
    conf = json.load(json_data_file)

TOKEN = conf['token']
PROXY = conf['proxy']
PROXY_ON = conf['proxy_on']
ID = conf['id']
MONGO = conf['mongo']
API = conf['api']
MTPROTO = conf['mtproto']

chats_dict = conf['chats']
CHATS = [chats_dict[i] for i in chats_dict]
