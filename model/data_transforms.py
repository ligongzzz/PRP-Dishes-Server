import torch
import torchvision
import torchvision.transforms as transforms
import PIL.Image as Image
import torchvision.transforms.functional as tf
import random
import numpy as np
import matplotlib.pyplot as plt


def transform_to_list(image, mask, size: int):
    image_list = []
    mask_list = []

    for _ in range(size):
        trans_image, trans_mask = transform(image, mask)
        image_list.append(trans_image)
        mask_list.append(trans_mask)

    return torch.stack(image_list), torch.stack(mask_list)


def transform(image, mask):
    # 自己写随机部分，50%的概率应用垂直，水平翻转。
    if random.random() > 0.5:
        image = tf.hflip(image)
        mask = tf.hflip(mask)
    if random.random() > 0.5:
        image = tf.vflip(image)
        mask = tf.vflip(mask)

    i, j, h, w = transforms.RandomResizedCrop.get_params(
        image, scale=(0.25, 1.0), ratio=(1, 1))
    image = tf.resized_crop(image, i, j, h, w, 256)
    mask = tf.resized_crop(mask, i, j, h, w, 256)
    image = tf.to_tensor(image)
    image = tf.normalize(image, [0.5], [0.5])
    mask = torch.from_numpy(np.array(mask)).type(torch.FloatTensor)

    return image, mask


def transform_to_img(x):
    transformer = transforms.ToPILImage()
    return transformer(x)
