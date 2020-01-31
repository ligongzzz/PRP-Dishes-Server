import numpy as np
import base64
import PIL.Image as Image
import torch
import torch.nn as nn
import random
import copy
import base64
import torchvision.models as models
import torchvision.transforms as transforms
from model.unet_model import *
import json


class dish_type():
    '''
    A class to storage the dish information.
    '''

    def __init__(self, name: str, nutrient_inform: dict):
        '''
        The cal,fat and weight are the real value in a dish. (After calculation.)
        '''
        self.name = name
        self.cal = nutrient_inform['cal'] * nutrient_inform['weight'] / 100
        self.fat = nutrient_inform['fat'] * nutrient_inform['weight'] / 100
        self.weight = nutrient_inform['weight']


img_cnt = 0

# Hyper Parameters
DEVICE = 'cpu'
IMG_SIZE = 256
OUT_FEATURES = 35

# Load the net.
net = UNet(3, OUT_FEATURES).to(DEVICE)
net.load_state_dict(torch.load('./net_param.pkl',
                               map_location=torch.device(DEVICE)))
print('Loaded the net successfully!')

# Load the labels.
labels = [i.replace('\n', '') for i in open(
    './labels.txt', 'rt').readlines()]

# Load the nutrient values.
nutrients = json.load(open('nutrient.json', 'rt'))

print('Labels and nutrient info loaded.')


def parse(src_data):
    global img_cnt
    img_data = base64.b64decode(src_data['data'])
    file_dir = f'./img/input{img_cnt}.png'
    file = open(file_dir, 'wb')
    file.write(img_data)
    file.close()

    # Set the input image.
    raw_img: Image.Image = Image.open(file_dir).convert('RGB')

    # Transform.
    transformer = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE), Image.NEAREST),
        transforms.ToTensor(),
        transforms.Normalize([0.5], [0.5])
    ])
    input_img = transformer(raw_img).to(DEVICE).unsqueeze(0)

    # Start UNet.
    print('Start UNet.')
    net.eval()
    with torch.no_grad():
        pred = net(input_img).squeeze()
        pred_img = torch.max(pred, 0)[1].to(
            'cpu').detach().unsqueeze(0).type(torch.uint8)
        print('Finished UNet.')

        menu_list = []
        for i in range(1, OUT_FEATURES):
            rate = torch.sum(pred_img == i).numpy() / IMG_SIZE ** 2
            if rate >= 0.03:
                menu_list.append(
                    dish_type(labels[i], nutrients[labels[i]]))

    # Add the img_cnt.
    img_cnt += 1

    return menu_list
