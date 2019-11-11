import numpy as np
import base64
import cv2

img_cnt = 0


def parse(src_data):
    global img_cnt
    img_data = base64.b64decode(src_data['data'])
    file_dir = f'./img/input{img_cnt}.png'
    file = open(file_dir, 'wb')
    file.write(img_data)
    file.close()

    img = cv2.imread(file_dir)

    split_cnt = 0
    for item in src_data['splitList']:
        print(img.shape, item['x'], item['y'], item['w'], item['h'])
        img_sub = img[int(item['y']):int(item['y'] + item['h']),
                      int(item['x']):int(item['x'] + item['w'])]
        cv2.imwrite(f'./img/output{img_cnt}_{split_cnt}.png', img_sub)
        split_cnt += 1

    img_cnt += 1
