import math

import PIL.Image
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from arcfutil import aff


def char2img(input_char, img_size=[100, 100], font_size=75, save=False):
    """
    字符转图片
    :param input_char: 输入字符串
    :param img_size: 图像大小
    :param font_size: 字体大小，宜与图片大小适配
    :param save: 如果遇到转换结果显示不全请切换save=True，查看生成图片是否完整
    :return:
    """
    img = Image.new("RGB", (img_size[0], img_size[1]), "white")
    draw_table = ImageDraw.Draw(im=img)
    draw_table.text(xy=(0, 0), text=input_char, fill='#000000', font=ImageFont.truetype('fonts/calibri.ttf', font_size))
    if save:
        img.save("fonts/%s.png" % input_char)
    return img.convert("L")


def pic2img(pic_path):
    """
    图片转PIL的img对象用于后续处理（灰度化）
    :param pic_path: 图片路径对象
    :return: PIL库的img
    """
    img = Image.open(pic_path).convert("L")
    return img


def img2point(img, threshold=1, center=True, scale=True):
    """
    图片转锚点，锚点用于连接黑线
    :param img: PIL.img格式的图像数据
    :param threshold: 转换阈值，阈值越大，过滤点越少，图像点越密集
    :param center: 图片是否居中显示
    :param scale: 是否对图像进行等比例缩放，如果为否，则按非等比例缩放
    :return: 锚点序列
    """
    # 裁剪
    if center:
        img = crop(img)

    arr = np.array(img)
    x_length, y_length = arr.shape
    x_proportion = 100 / y_length
    y_proportion = 100 / x_length
    if scale:
        x_proportion = min(x_proportion, y_proportion)
        y_proportion = min(x_proportion, y_proportion)

    target_points = []
    for y_i, y in enumerate(arr):
        for x_i, x in enumerate(y):
            if x < 150:
                target_points.append([round(x_i * x_proportion), round(y_i * y_proportion)])

    # 锚点
    anchor = []
    while target_points:
        top = target_points[0]
        anchor.append(top)
        for p_i, p in enumerate(target_points):
            if distance(p, top) < threshold:
                target_points.pop(p_i)

    print("锚点转化成功！")
    return anchor


def point2arc(points, start_time, duration, add_x=0, add_y=0):
    """
    锚点连接为黑线
    :param points:锚点序列
    :param start_time: 开始时间
    :param duration: 持续时长
    :param add_x: 整体横向偏移
    :param add_y: 整体纵向偏移
    :return: 转化后的arc物件列表
    """
    arclist = []
    max_y = 0
    for p_i, p in enumerate(points):
        # 获取长度用于时间缩放
        max_y = max(max_y, points[p_i][1])

    for p_i, p in enumerate(points):
        # 转为三元组，前两项为平面位置，后一项为投影时的y坐标
        points[p_i] = [points[p_i][0], points[p_i][1], max_y - points[p_i][1]]

    pairs = []
    next_i = 0

    while next_i >= 0:
        top = points[next_i]
        points.pop(next_i)
        if points:
            cur_distance = 10000
            for p_i, p in enumerate(points):
                if distance(p, top) < cur_distance:
                    pair_i = p_i
                    cur_distance = distance(p, top)
            if cur_distance < 50:
                pairs.append((top, points[pair_i]))
            next_i = pair_i
        else:
            next_i = -1

    print("锚点匹配成功！")

    for p_i, p in enumerate(pairs):
        first_time = start_time + round((1 - p[0][1] / max_y) * duration)
        second_time = start_time + round((1 - p[1][1] / max_y) * duration)
        if first_time > second_time:
            new_arc = aff.Arc(time=second_time, totime=first_time,
                              fromx=p[1][0] / 100 + add_x, fromy=p[1][2] / 100 + add_y, tox=p[0][0] / 100 + add_x, toy=p[0][2] / 100 + add_y,
                              slideeasing="s", isskyline=True, skynote=[], color=1)
        else:
            new_arc = aff.Arc(time=first_time, totime=second_time,
                              fromx=p[0][0] / 100 + add_x, fromy=p[0][2] / 100 + add_y, tox=p[1][0] / 100 + add_x, toy=p[1][2] / 100 + add_y,
                              slideeasing="s", isskyline=True, skynote=[], color=1)
        arclist.append(new_arc)

    print("黑线物件生成成功！")

    return arclist


def distance(p, q):
    """
    两个定位点的距离平方
    :param p: 定位点1
    :param q: 定位点2
    :return: 两个定位点距离的平方
    """
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


def crop(img):
    """
    图片裁剪
    :param img: PIL.img格式的图片数据
    :return: 裁剪空白后的图片数据
    """
    arr = np.array(img)
    position = [np.shape(arr)[0], np.shape(arr)[1], 0, 0]

    for y_i, y in enumerate(arr):
        for x_i, x in enumerate(y):
            if not x:
                position[0] = min(x_i, position[0])
                position[1] = min(y_i, position[1])
                position[2] = max(x_i, position[2])
                position[3] = max(y_i, position[3])

    if position[0] < position[2] and position[1] < position[3]:
        return img.crop((position[0], position[1], position[2], position[3]))
    else:
        return img


# 存放物件列表，用于存储转换生成后的语句对象
aff_object_list = []
# 过滤时使用的距离阈值，该值越大，锚点越多
distance_threshold = 30
# 黑线物件的持续时间
duration = 250
# 生成指定字符的
for c_i, c in enumerate(["A", "B", "C"]):
    # 将字母转换为图片
    m = char2img(c)
    # 图片转换为定位锚点
    t = img2point(m, threshold=distance_threshold)
    # 定位锚点转换为黑线物件
    al = point2arc(points=t, start_time=200 + 1500 * c_i, duration=duration, add_x=0.25)
    # 黑线物件添加到物件列表
    aff_object_list = aff_object_list + al

# 读取图片
m = pic2img(pic_path="fonts/test.png")
# 图片转换为定位锚点
t = img2point(m, threshold=distance_threshold, scale=False)
# 定位锚点转换为黑线物件
al = point2arc(points=t, start_time=7000, duration=duration, add_y=0.25)
# 黑线物件添加到物件列表
aff_object_list = aff_object_list + al
# 添加时间戳
aff_object_list.append(aff.Timing(0, 100))
# 保存文件
aff.dumps(aff.AffList(aff_object_list), r'0.aff')
