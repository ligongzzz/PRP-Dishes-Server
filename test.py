import asyncio
import websockets
import ssl
import base64
import json
import numpy as np
import requests
import random
import time
import pickle
import threading
import parse_img


class cal_type():
    def __init__(self, value: int, t):
        self.val = value
        self.t = t


class user_type():
    def __init__(self, userID):
        self.userID: str = userID
        self.cal_list = []


user_list = {}

# A func to save user info.


def save_user_info(seconds: int):
    while True:
        time.sleep(seconds)
        try:
            to_save = pickle.dumps(user_list)
            f_o = open('user_data.dat', 'wb')
            f_o.write(to_save)
            f_o.close()
        except Exception as err:
            print(err)
            print('用户数据保存失败！')


threading.Thread(target=save_user_info, args=(20,)).start()

try:
    f_i = open('user_data.dat', 'rb')
    user_list_pkl = f_i.read()
    f_i.close()
    user_list = pickle.loads(user_list_pkl)
    print('加载用户数据成功！')
except Exception as err:
    print(err)
    print('加载用户数据失败！')


async def hello(websocket, path):
    print('Received user.')
    # Set The User ID
    userID = None
    while True:
        try:
            name = await websocket.recv()
            print('<', len(name))
            src_data = json.loads(name)
            print(src_data['type'])
            if src_data['type'] == 'img':
                if userID is None:
                    greeting = json.dumps({'type': "img", 'result': 0})
                    await websocket.send(greeting)
                    print('>', greeting)
                    continue

                parse_img.parse(src_data)

                # Do Something...
                cal_val = random.randint(0, 1600)
                t = time.localtime(time.time())

                try:
                    user_list[userID].cal_list.append(cal_type(cal_val, t))
                    print('用户数据已经写入数据库！')
                except Exception as err:
                    print(err)
                    print('写入数据库时发生错误！')

                greeting = {'type': 'img', 'result': 1, 'data': [
                    '西红柿炒蛋', '红烧肉', '青菜', '鸡腿'], 'cal_val': cal_val}

                greeting = json.dumps(greeting)

                await websocket.send(greeting)
                print(f"> {greeting}")

                # Send New Cal Message
                return_data = {}
                return_data['type'] = 'day_cal'
                cur_time = time.localtime(time.time())
                day_cal_val = 0
                for item in user_list[userID].cal_list:
                    if item.t.tm_year == cur_time.tm_year and item.t.tm_mon == cur_time.tm_mon and item.t.tm_mday == cur_time.tm_mday:
                        day_cal_val += item.val
                return_data['val'] = day_cal_val
                return_data = json.dumps(return_data)
                await websocket.send(return_data)
                print('>', return_data)
            elif src_data['type'] == 'login':
                try:
                    f_id = open('appid.txt', 'rt')
                    app_id = f_id.read()
                    f_id.close()
                    f_id = open('secret_key.txt', 'rt')
                    secret_key = f_id.read()
                    f_id.close()
                    code = src_data['code']
                    print('code:', code)
                    get_txt = requests.get(
                        f'https://api.weixin.qq.com/sns/jscode2session?appid={app_id}&secret={secret_key}&js_code={code}&grant_type=authorization_code').text
                    received_json = json.loads(get_txt)
                    print('<', received_json)
                    userID = received_json['openid']

                    if user_list.get(userID) is None:
                        user_list[userID] = user_type(userID)
                        print('已经添加新用户:', userID)

                    else:
                        print('老用户：', userID)

                    return_msg = {"type": "login",
                                  "result": 1}
                    return_msg = json.dumps(return_msg)
                    await websocket.send(return_msg)
                    print('>', return_msg)
                except Exception as err:
                    print(err)
                    return_msg = {"type": "login", "result": 0}
            elif src_data['type'] == 'cal':
                return_data = {}
                try:
                    if src_data['class'] == 'normal':
                        return_data['type'] = 'cal'
                        return_data['result'] = 1
                        return_list = []
                        for item in user_list[userID].cal_list:
                            cur_item = {}
                            cur_item['val'] = item.val
                            cur_item['year'] = item.t.tm_year
                            cur_item['mon'] = item.t.tm_mon
                            cur_item['day'] = item.t.tm_mday
                            cur_item['hour'] = item.t.tm_hour
                            cur_item['min'] = item.t.tm_min
                            return_list.append(cur_item)

                        cur_time = time.localtime(time.time())
                        day_cal_val = 0
                        for item in user_list[userID].cal_list:
                            if item.t.tm_year == cur_time.tm_year and item.t.tm_mon == cur_time.tm_mon and item.t.tm_mday == cur_time.tm_mday:
                                day_cal_val += item.val
                        return_data['day_cal'] = day_cal_val
                        if len(return_list) > 15:
                            return_list = return_list[-15:]
                        return_data['data'] = return_list
                    elif src_data['class'] == 'day':
                        return_data['type'] = 'day_cal'
                        cur_time = time.localtime(time.time())
                        day_cal_val = 0
                        for item in user_list[userID].cal_list:
                            if item.t.tm_year == cur_time.tm_year and item.t.tm_mon == cur_time.tm_mon and item.t.tm_mday == cur_time.tm_mday:
                                day_cal_val += item.val
                        return_data['val'] = day_cal_val

                    return_data = json.dumps(return_data)
                    await websocket.send(return_data)
                    print('>', return_data)

                except Exception as err:
                    print(err)
                    await websocket.send(json.dumps({'type': 'cal', 'result': 0}))
        except Exception as err:
            print(err)
            break
    print('Connection closed.')

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile='./a.pem', keyfile='./a.key')

start_server = websockets.serve(
    hello, '0.0.0.0', 80, ssl=ssl_context, read_limit=2**25, max_size=2**25)
print('start service...')
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
