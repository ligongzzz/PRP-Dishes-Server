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
import queue


class cal_type():
    def __init__(self, value: int, t):
        self.val = value
        self.t = t


class user_type():
    def __init__(self, userID):
        self.userID: str = userID
        self.cal_list = []


# A computer type to storage the basic computer info.
class computer_type:
    def __init__(self, websocket):
        self.websocket = websocket
        self.cur_result = None
        self.computer_status = True

    async def process_img(self, src_data):
        # Clear the current result.

        raw_data = json.dumps(src_data)
        await self.websocket.send(raw_data)
        print('Data sent to the computer.')

        # While True receive the result from the computer.
        while self.cur_result is None:
            await asyncio.sleep(0.001)

            # Check if the computer is down.
            if not self.computer_status:
                print('The computer service is down.')
                raise Exception('Network Error.')

        print('Received the result from the computer.')
        src_data = self.cur_result
        self.cur_result = None

        if src_data['type'] == 'process_result' and src_data['result'] == 'success':
            return src_data['data'], src_data['cal_val']
        else:
            print('Computer network error.')
            raise Exception("Network Error.")


# A list to storage the users.
user_list = {}

# A queue to storage the available computation sources.
computer_queue = []


async def process_image(src_data):
    '''
    A function to process the image with the computer.
    Return: pred_data, cal_val.
    '''
    # If the computer queue is empty, then just compute with CPU on this server :(
    if len(computer_queue) == 0:
        pred_data = parse_img.parse(src_data)
        cal_val = random.randint(0, 1600)
        return pred_data, cal_val
    else:
        # Get a computer from the computer queue.
        cur_computer: computer_type = computer_queue[0]
        computer_queue.remove(cur_computer)
        pred_data, cal_val = await cur_computer.process_img(src_data)
        # Put the computer into the queue.
        computer_queue.append(cur_computer)
        return pred_data, cal_val


def save_user_info(seconds: int):
    """
    A function to save user info.
    """
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
    print('Successfully loaded user data!')
except Exception as err:
    print(err)
    print('User data loading failed!')


async def main_service_loop(websocket, path):
    print('Received user.')
    # Set The User ID
    userID = None
    cur_computer: computer_type = None
    while True:
        try:
            name = await websocket.recv()
            print('<', end=' ')
            src_data = json.loads(name)
            print(src_data['type'])
            if src_data['type'] == 'img':
                if userID is None:
                    greeting = json.dumps({'type': "img", 'result': 0})
                    await websocket.send(greeting)
                    print('>', greeting)
                    continue

                # Process the images to get the answer.
                try:
                    pred_data, cal_val = await process_image(src_data)
                except Exception as err:
                    print(err)
                    print('Error when processing the images.')
                    await websocket.send(json.dumps({'type': 'img', 'result': 0}))
                    continue

                t = time.localtime(time.time())

                try:
                    user_list[userID].cal_list.append(cal_type(cal_val, t))
                    print('用户数据已经写入数据库！')
                except Exception as err:
                    print(err)
                    print('写入数据库时发生错误！')

                greeting = {'type': 'img', 'result': 1,
                            'data': pred_data, 'cal_val': cal_val}

                greeting = json.dumps(greeting)
                await websocket.send(greeting)

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
                    print('> cal data')

                except Exception as err:
                    print(err)
                    await websocket.send(json.dumps({'type': 'cal', 'result': 0}))
            elif src_data['type'] == 'computer':
                cur_computer = computer_type(websocket)
                computer_queue.append(cur_computer)
                print('Received a new computer.')
            elif src_data['type'] == 'process_result':
                cur_computer.cur_result = src_data
        except Exception as err:
            print(err)
            break

    # Remove the computer from the computer queue.
    if cur_computer is not None:
        cur_computer.computer_status = False
        if cur_computer in computer_queue:
            computer_queue.remove(cur_computer)
        print('Removed the computer from the computer queue.')

    print('Connection closed.')

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(certfile='./a.pem', keyfile='./a.key')

start_server = websockets.serve(
    main_service_loop, '0.0.0.0', 82, ssl=ssl_context, read_limit=2**25, max_size=2**25)
print('start service...')
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
