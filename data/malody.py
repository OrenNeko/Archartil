# Malody谱面格式： https://www.bilibili.com/read/cv8257852/
# Malody谱面下载： https://cbo17ty22x.feishu.cn/wiki/wikcncFuigGA1V7C9ffxcnWHSvd

# 此代码用于批量转换Malody谱面为Pickel格式

import json
import os
import pickle
import zipfile

import arcfutil.aff
import librosa

data_path = "Malody_Key(4K)"


def unpack():
    # malody谱面格式为mcz，改后缀名为zip后解压
    for chart_file in os.listdir(data_path):
        chart_mcz = os.path.join(data_path, chart_file)
        chart_zip = os.path.splitext(chart_mcz)[0] + ".zip"
        os.rename(chart_mcz, chart_zip)
        f = zipfile.ZipFile(chart_zip, 'r')
        f.extractall(path=os.path.splitext(chart_mcz)[0])
        f.close()


def note2format(notes, bpm):
    """
    转换为统一格式
    :param notes: malody的节点列表
    :param bpm: 谱面bpm
    :return: 转换后的谱面格式
    """
    four_beats_interval = 60000 / bpm
    note_list = []
    for n in notes:
        if "column" in n:
            track = n["column"]
            note_type = "tap"
            start_time = n["beat"][0] * four_beats_interval + n["beat"][1] * four_beats_interval / n["beat"][2]
            if "endbeat" in n:
                note_type = "hold"
                end_time = n["endbeat"][0] * four_beats_interval + n["endbeat"][1] * four_beats_interval / n["endbeat"][2]

            if note_type == "tap":
                note_list.append({"note_type": note_type, "track": track, "time": start_time})
            elif note_type == "hold":
                note_list.append({"note_type": note_type, "track": track, "time": start_time, "end_time": end_time})

    return note_list


def save():
    malody_4k = []
    part = 1
    for chart_dir in os.listdir(data_path):
        ab_chart_dir = os.path.join(data_path, chart_dir)
        if os.path.isdir(ab_chart_dir):
            try:
                # 每首歌曲建立一个索引
                new_song = {"song_id": chart_dir, "mode": "4K", "charts": []}
                inner_dir = os.path.join(ab_chart_dir, "0")
                for f in os.listdir(inner_dir):
                    if f.endswith(".mc"):
                        mc_path = os.path.join(inner_dir, f)
                        with open(mc_path, "r", encoding="utf-8") as mc_file:
                            mc_data = json.load(mc_file)
                        for t in mc_data["time"]:
                            if t["beat"][0] == 0 and t["beat"][1] == 0:
                                bpm = t["bpm"]
                        notes = mc_data["note"]
                        for n in notes:
                            if "offset" in n:
                                offset = n["offset"]

                        difficulty = mc_data["meta"]["version"]
                        note_format = note2format(notes, bpm)

                        new_chart = {"bpm": bpm, "difficulty": difficulty, "note": note_format, "offset": -offset}
                        new_song["charts"].append(new_chart)

                    if f.endswith(".ogg"):
                        song_path = os.path.join(inner_dir, f)
                        new_song["song"] = librosa.load(song_path, sr=44100)

                malody_4k.append(new_song)
                print(len(malody_4k))
                if len(malody_4k) == 200:
                    with open("melody_4k_part%d.pickle" % part, "wb") as m4k:
                        pickle.dump(malody_4k, m4k)
                    part += 1
                    malody_4k = []
                    print(part)


            except Exception as e:
                print(e)

    with open("melody_4k_part%d.pickle" % part, "wb") as m4k:
            pickle.dump(malody_4k, m4k)


def mc2aff(mc_path):
    with open(mc_path, "r", encoding="utf-8") as mc_file:
        mc_data = json.load(mc_file)
    for t in mc_data["time"]:
        if t["beat"][0] == 0 and t["beat"][1] == 0:
            bpm = t["bpm"]
    notes = mc_data["note"]
    four_beats_interval = 60000 / bpm
    note_list = [arcfutil.aff.Timing(0, bpm)]
    for n in notes:
        if "offset" in n:
            offset = n["offset"]
        if "column" in n:
            track = n["column"] + 1
            note_type = "tap"
            start_time = n["beat"][0] * four_beats_interval + n["beat"][1] * four_beats_interval / n["beat"][2]
            if "endbeat" in n:
                note_type = "hold"
                end_time = n["endbeat"][0] * four_beats_interval + n["endbeat"][1] * four_beats_interval / n["endbeat"][2]

            if note_type == "tap":
                note_list.append(arcfutil.aff.Tap(start_time, track))
            elif note_type == "hold":
                note_list.append(arcfutil.aff.Hold(start_time, end_time, track))


    aff_obj = arcfutil.aff.AffList(note_list)
    aff_obj.offset = - offset
    arcfutil.aff.dumps(aff_obj, os.path.join(os.path.dirname(mc_path), "0.aff"))


# save()
mc2aff(r"D:\LIFE\2022\Affcat\data\TEST\malody\_song_1369\0\1507024911.mc")
