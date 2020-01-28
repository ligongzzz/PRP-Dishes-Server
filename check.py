import torch
import torch.nn as nn
from model.unet_model import *
import PIL.Image as Image
import matplotlib.pyplot as plt
import numpy as np
import torchvision
import torchvision.transforms as transforms
import os

plt.rcParams['font.family'] = ['sans-serif']
plt.rcParams['font.sans-serif'] = ['SimHei']

# Hyper Parameters
DEVICE = 'cuda'
IMG_SIZE = 256
OUT_FEATURES = 17

# Load the net.
net = UNet(3, OUT_FEATURES).to(DEVICE)
net.load_state_dict(torch.load('./net_param.pkl'))
print('Loaded the net successfully!')

# Load the labels.
labels = [i.replace('\n', '') for i in open(
    './labels.txt', 'rt').readlines()]
labels.remove(labels[0])

for root, dirs, files in os.walk('./test_img'):
    for f in files:
        if not f.endswith('.jpg'):
            continue

        # Set the input image.
        raw_img: Image.Image = Image.open('./test_img/' + f)

        # Transform.
        transformer = transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE), Image.NEAREST),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5])
        ])
        input_img = transformer(raw_img).to(DEVICE).unsqueeze(0)

        print('Loaded the image successfully!')

        # Start UNet.
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

            print(menu_list)

            # Show the result.
            transform_to_img = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize(
                    (raw_img.height, raw_img.width), Image.NEAREST)
            ])
            pred_img = transform_to_img(pred_img)

            plt.subplot(1, 2, 1)
            plt.title('origin')
            plt.imshow(raw_img)
            plt.subplot(1, 2, 2)
            plt.title('pred')
            plt.imshow(pred_img)
            plt.suptitle('识别结果：' + ' '.join(menu_list))
            plt.show()
