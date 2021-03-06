import time

from flask import Flask, request
from flask_cors import CORS, cross_origin
import json
import os
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
mongo = MongoClient(os.environ['MONGODB_ADDRESS'])
mongo_collection = 'test'


@app.route('/', methods=['post'])
def main() -> str:
    if request.json['action'] == 'login':
        return json.dumps(login(request.json['payload']), ensure_ascii=False)
    if request.json['action'] == 'register':
        return json.dumps(register(request.json['payload']), ensure_ascii=False)
    if request.json['action'] == 'sync':
        return json.dumps(sync(request.json['payload']), ensure_ascii=False)
    else:
        return json.dumps({'ok': False})


def login(data: dict) -> dict:
    """
    Example post (with python requests):
    res = requests.post('http://server.url', headers={'Content-Type': 'application/json', json={'action': 'login',
    'payload': {'uid': '1139442593200172297', 'inventory': {}, 'last_update': time.time()}}})
    """
    mongo_res = mongo['inventory'][mongo_collection].find_one({'uid': data['uid']})
    if not mongo_res:
        return {'ok': False, 'msg': 'uid not found, use register instead.'}
    mongo_res.pop('_id')
    return {'ok': True, 'data': mongo_res}


def register(data: dict) -> dict:
    """
    Registering is a simplified one here. We don't use traditional username - password schema. Instead,
    a random uid is given to user for cross device synchronize.
    Example post (with python requests):
    res = requests.post('http://server.url', headers={'Content-Type': 'application/json'}, json={'action': 'register',
    'payload': {'uid': '0', 'inventory': {'apple': {'name': 'apple', 'content': '123'}, 'peach':
    {'name': 'peach', 'content': '3'}}, 'last_update': time.time()}})
    """
    reg_time = time.time()
    uid = str(hash(reg_time))
    res = mongo['inventory'][mongo_collection].find_one({'uid': data['uid']})
    if res:
        return {'ok': False, 'msg': 'uid exists, use sync instead.'}

    print(data)
    mongo['inventory'][mongo_collection].insert_one({'uid': uid, 'inventory': data['inventory'], 'last_update': reg_time})
    return {'ok': True, 'data': {'uid': uid, 'inventory': data['inventory'], 'last_update': reg_time}}


def sync(data: dict) -> dict:
    """
    Example post (with python requests)
    res = requests.post('http://server.url', headers={'Content-Type': 'application/json'}, json={'action': 'sync', 'payload': {
     'uid': '1139442593200172297', 'inventory': {'apple': {'name': 'apple', 'content': '123'}, 'peach': {'name': 'peach'
     , 'content': '3'}}, 'last_update': time.time()}})
    """
    res = mongo['inventory'][mongo_collection].find_one({'uid': data['uid']})
    if not res:
        return {'ok': False, 'msg': 'uid not found, use register instead.'}
    if float(res['last_update']) < float(data['last_update']):
        mongo['inventory'][mongo_collection].find_one_and_replace({'uid': data['uid']}, data)
        return {'ok': True, 'data': data}
    else:
        res.pop('_id')
        return {'ok': True, 'data': res}


if __name__ == '__main__':
    app.run(port=int(os.environ['PORT']), host='0.0.0.0')
