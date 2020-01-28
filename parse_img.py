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


img_cnt = 0

# Hyper Parameters
DEVICE = 'cpu'
IMG_SIZE = 256
OUT_FEATURES = 17

# Load the net.
net = UNet(3, OUT_FEATURES).to(DEVICE)
net.load_state_dict(torch.load('./net_param.pkl',
                               map_location=torch.device(DEVICE)))
print('Loaded the net successfully!')

# Load the labels.
labels = [i.replace('\n', '') for i in open(
    './labels.txt', 'rt').readlines()]
labels.remove(labels[0])


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
                menu_list.append(labels[i])

    return menu_list
