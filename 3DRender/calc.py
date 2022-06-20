#################################################
# 计算心胸比
# call: http://your-domain:port/ctr/filename.jpg
#################################################
import math
import cv2
from loguru import logger
import numpy as np
import paddleseg.transforms as T
from SimpleITK import ReadImage, GetArrayFromImage
from paddle import set_device, disable_static, load, to_tensor
from paddleseg.models import UNet

cpu = set_device("cpu")
disable_static(cpu)

# 原图最大边缩至512
transforms = T.Compose([
    T.ResizeByLong(512),
    T.Normalize()
])

model = UNet(num_classes=3)
model_path = "model.pdparams"


# dicom转jpg
def convert_from_dicom_to_jpg(img, low_window, high_window):
    lungwin = np.array([low_window * 1., high_window * 1.])
    newimg = (img - lungwin[0]) / (lungwin[1] - lungwin[0])  # 归一化
    newimg = (newimg * 255).astype('uint8')  # 将像素值扩展到[0,255]
    # cv2.imwrite(save_path, newimg, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
    return newimg


# 读取DICOM文件
def dcmread(dcm_path):
    ds_array = ReadImage(dcm_path)  # 读取dicom文件的相关信息
    img_array = GetArrayFromImage(ds_array)  # 获取array
    print(ds_array.GetMetaData("0018|1164"))
    print(ds_array.GetMetaData("0028|0030"))
    # SimpleITK读取的图像数据的坐标顺序为zyx，即从多少张切片到单张切片的宽和高，此处我们读取单张，因此img_array的shape
    # 类似于 （1，height，width）的形式
    shape = img_array.shape
    img_array = np.reshape(img_array, (shape[1], shape[2]))  # 获取array中的height和width
    high_window = np.max(img_array)
    low_window = np.min(img_array)
    return convert_from_dicom_to_jpg(img_array, low_window, high_window)


# 预测
def predict(model, model_path, image):
    para_state_dict = load(model_path)
    model.set_dict(para_state_dict)
    model.eval()
    # im = dcmread(im_path)
    im, _ = transforms(image)
    im = im[np.newaxis, ...]
    im = to_tensor(im)
    output = model(im)[0]
    output = output.numpy()
    output = np.argmax(output, axis=1)
    output = output.transpose(1, 2, 0)
    return output


# 找到最大的轮廓
def find_max_area(contours):
    area = []
    for k in range(len(contours)):
        area.append(cv2.contourArea(contours[k]))
    max_idx = np.argmax(np.array(area))
    return max_idx


# 运算去除噪声
def morph_open(threshold):
    kernel = np.ones((3, 3), np.uint8)
    threshold = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel, iterations=3)
    return threshold


# 计算最左和最后的点, 外边距的x,y,w,h
def get_left_right(cnt):
    left = tuple(cnt[cnt[:, :, 0].argmin()][0])
    right = tuple(cnt[cnt[:, :, 0].argmax()][0])
    x, y, w, h = cv2.boundingRect(cnt)
    return (left, right, x, y, w, h)


# 找出右膈肌顶的位置
def calc_diaphragm(image, hy, cx, cw, step):
    im = image.copy()
    width = int(cw / 8)
    while True:
        im = image[hy:hy + step, cx + width:cx + width * 2]
        no_black_pixels = cv2.countNonZero(im)
        if no_black_pixels < int(width * step * 0.95):
            return hy + step
        hy = hy + step


def get_ctr(im_path):
    dicom_image = ReadImage(im_path)  # 读取dicom文件的相关信息
    pixelspaceing = None
    if dicom_image.HasMetaDataKey("0028|0030"):
        pixelspaceing = dicom_image.GetMetaData("0028|0030").split('\\')[0]
    else:
        pixelspaceing = dicom_image.GetMetaData("0018|1164").split('\\')[0]
    print(pixelspaceing)
    img_array = GetArrayFromImage(dicom_image)  # 获取array
    # SimpleITK读取的图像数据的坐标顺序为zyx，即从多少张切片到单张切片的宽和高，此处我们读取单张，因此img_array的shape
    # 类似于 （1，height，width）的形式
    shape = img_array.shape
    img_array = np.reshape(img_array, (shape[1], shape[2]))  # 获取array中的height和width
    high_window = np.max(img_array)
    low_window = np.min(img_array)
    # image = cv2.imread(im_path)
    image = convert_from_dicom_to_jpg(img_array, low_window, high_window)
    output = predict(model, model_path, image)

    w, h = output.shape[0], output.shape[1]
    segmentation = np.zeros((w, h, 1), np.uint8)
    #
    resizeLong = T.ResizeByLong(512)
    image = resizeLong(image)[0]

    segmentation[:, :, 0] = output[:, :, 0]
    segmentation = np.squeeze(segmentation)

    # 找出心脏位置
    ret, heart = cv2.threshold(segmentation, 1, 255, 0)
    heart = morph_open(heart)
    contours, hierarchy = cv2.findContours(heart, 1, 2)
    max_idx = find_max_area(contours)
    heart = contours[max_idx]
    left_heart, right_heart, hx, hy, WidthHeart, hh = get_left_right(heart)

    # 找出肺部位置
    img_temp = segmentation.copy()
    w, h = img_temp.shape[0], img_temp.shape[1]
    ret, chest = cv2.threshold(img_temp, 0, 255, 0)
    chest = morph_open(chest)
    contours, hierarchy = cv2.findContours(chest, 1, 2)
    max_idx = find_max_area(contours)
    chest = contours[max_idx]
    left_chest, right_chest, cx, cy, WidthChest, ch = get_left_right(chest)

    position_y = calc_diaphragm(img_temp, left_heart[1], left_chest[0], WidthChest, 5)
    ret, chest = cv2.threshold(img_temp[:position_y, :], 0, 255, 0)
    chest = morph_open(chest)
    contours, hierarchy = cv2.findContours(chest, 1, 2)
    max_idx = find_max_area(contours)
    chest = contours[max_idx]
    left_chest, right_chest, cx, cy, WidthChest, ch = get_left_right(chest)
    ctr_obj = {
        "width": shape[2],
        "height": shape[1],
        "h_zoom": shape[1]/512,
        "w_zoom": shape[2]/512,
        "pixelspaceing": float(pixelspaceing),
        "heart": {
            "left": [math.ceil(left_heart[0]), math.ceil(left_heart[1])],
            "right": [math.ceil(right_heart[0]), math.ceil(right_heart[1])],
            "rect": [math.ceil(hx), math.ceil(hy)],
            "width": math.ceil(WidthHeart),
            "height": math.ceil(hh),
        },
        "chest": {
            "left": [math.ceil(left_chest[0]), math.ceil(left_chest[1])],
            "right": [math.ceil(left_chest[0] + WidthChest), math.ceil(left_chest[1])],
            "rect": [math.ceil(cx), math.ceil(cy)],
            "width": math.ceil(WidthChest),
            "height": math.ceil(ch),
        }
    }
    return ctr_obj


if __name__ == '__main__':
    logger.info("开始")
    print(get_ctr("D:\\c-get\\2.dcm"))
    logger.info("开始2")
