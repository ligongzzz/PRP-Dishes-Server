import numpy as np
import base64
import cv2
import torch
import torch.nn as nn
import random
import copy
import base64
import torchvision.models as models
import torchvision.transforms as transforms


img_cnt = 0

resnet = models.resnet50()
resnet.fc = nn.Linear(2048, 22)
resnet.eval()


def random_img_generator(img, length, n):
    ans_list = []
    for _ in range(n):
        cur_img: np.ndarray = copy.copy(img)
        # Size Random
        rand_len = random.randint(length, 2 * length)
        cur_img = cv2.resize(cur_img, (rand_len, rand_len))
        # Pos Random
        rand_x = random.randint(0, rand_len - length)
        rand_y = random.randint(0, rand_len - length)
        cur_img = cur_img[rand_x:rand_x + length, rand_y:rand_y + length, :]
        # Color Random
        rand_color = random.random()*0.3
        if random.random() < 0.5:
            cur_img = cur_img * (1.0 - rand_color)
        else:
            cur_img = cur_img + (255 - cur_img) * rand_color
        # Direction Random
        rand_d = random.randint(0, 2)
        if rand_d == 1:
            cur_img = np.flipud(cur_img)
        elif rand_d == 2:
            cur_img = np.fliplr(cur_img)
        cur_img = cur_img.astype(np.uint8)
        ans_list.append(cur_img)
    return ans_list


resnet.load_state_dict(torch.load('./net_param.pkl'))
print('已经成功加载网络!')
menu_list = open('menu.txt', 'rt').readlines()


def parse_img(img_data):
    img_list = random_img_generator(img_data, 224, 5)
    print('Start recognition.')
    data = np.empty((5, 3, 224, 224))

    trans_to_tensor = transforms.ToTensor()
    trans_normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                           std=[0.229, 0.224, 0.225])

    for i in range(5):
        data[i] = trans_normalize(trans_to_tensor(img_list[i]))

    torch_data = torch.from_numpy(data).type(torch.FloatTensor)
    pred = torch.mean(resnet(torch_data), 0)
    pred = torch.max(pred, 0)[1].detach().numpy()
    print('Finish:', pred)
    return pred


def parse(src_data):
    global img_cnt
    img_data = base64.b64decode(src_data['data'])
    file_dir = f'./img/input{img_cnt}.png'
    file = open(file_dir, 'wb')
    file.write(img_data)
    file.close()

    img = cv2.imread(file_dir)

    split_cnt = 0
    ans_list = []

    for item in src_data['splitList']:
        img_sub = img[int(item['y']):int(item['y'] + item['h']),
                      int(item['x']):int(item['x'] + item['w'])]
        cv2.imwrite(f'./img/output{img_cnt}_{split_cnt}.png', img_sub)

        img_sub = cv2.cvtColor(img_sub, cv2.COLOR_BGR2RGB)
        pred = parse_img(img_sub)
        if pred != 0:
            ans_list.append(menu_list[pred])
            cv2.rectangle(img, (int(item['x']), int(item['y'])), (int(
                item['x'] + item['w']), int(item['y'] + item['h'])), (255, 0, 0), 2)

        split_cnt += 1

    img_cnt += 1
    img = cv2.transpose(img)
    img = cv2.flip(img, 0)
    img = cv2.resize(img, (200, 100))
    # img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    cv2.imwrite('tmp_file.png', img)
    f = open('tmp_file.png', 'rb')
    img_str = 'data:image/png;base64,' + \
        str(base64.b64encode(f.read()), encoding='ascii')
    f.close()

    return ans_list, img_str
