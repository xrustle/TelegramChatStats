from pymongo import MongoClient

item = {'_id': 7,
        'name': 'test2'}

client = MongoClient(host="localhost", port=27018)
db = client.get_database('test')

_id = item['_id']
del item['_id']
result = db['test'].update_one({'_id': _id},
                               {'$set': item},
                               upsert=True)

if result.raw_result['updatedExisting']:
    print('Updated')
else:
    print('Added')

