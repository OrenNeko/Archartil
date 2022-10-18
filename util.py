import random

from arcfutil import aff


def times_to_aff(times_list, last_side=random.randint(0, 1), overlap=False):
    """
    时间序列转AFF，使用随机交互排键
    :param times_list: 传输时间序列
    :param last_side: 上次起手位置
    :param overlap: 是否允许叠键
    """
    afflist = []
    if last_side == 0:
        # 左起手
        last_lane = 1
    else:
        # 右起手
        last_lane = 4

    for t in times_list:
        if last_side == 0:
            # 向右侧布键
            if overlap:
                next_lane = random.randint(last_lane, 4)
            else:
                next_lane = random.randint(last_lane + 1, 4)
            new_note = aff.Tap(time=t, lane=next_lane)
        else:
            # 向左侧布键
            if overlap:
                next_lane = random.randint(1, last_lane)
            else:
                next_lane = random.randint(1, last_lane - 1)
            new_note = aff.Tap(time=t, lane=next_lane)

        last_side = 1 - last_side
        last_lane = next_lane

        afflist.append(new_note)

    return afflist


def save_afflist(save_path, afflist, offset, bpm):
    """
    保存AFF列表
    :param bpm: BPM
    :param save_path: 保存路径
    :param afflist: AFF列表
    :param offset: 偏置
    """
    afflist.append(aff.Timing(0, bpm))
    # afflist.append(aff.Timing(offset, bpm))
    aff_obj = aff.AffList(afflist)
    aff_obj.offsetto(offset)
    aff_obj.align(bpm=bpm)
    aff.dumps(aff_obj, save_path)
