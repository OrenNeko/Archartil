# https://tieba.baidu.com/p/2962677101?pid=49184899657&cid=0#49184899657
# 感谢@灲燚的RM谱面解析教程

import binascii
import os
import pickle
import struct
import copy
import arcfutil.aff
import librosa
from arcfutil import aff


def bin2hex(imd_file):
    bin = open(imd_file, 'rb')
    hex_list = ("{:02X}".format(int(c)) for c in bin.read())
    bin.close()
    buf_list = list(hex_list)
    return buf_list


def parse(hex_list):
    # 谱面总时间
    song_time = int("".join(hex_list[0:4][::-1]), 16)
    # 谱面总拍数/时间戳行数
    beats_num = int("".join(hex_list[4:8][::-1]), 16)
    # 时间戳序列
    line_id = 0
    for i, j in enumerate(hex_list[8:]):
        if i % 12 == 0 and line_id < beats_num:
            timestamp = int("".join(hex_list[i + 8:i + 12][::-1]), 16)
            beats_per_minute = struct.unpack('d', binascii.unhexlify("".join(hex_list[i + 12:i + 20])))[0]
            line_id = line_id + 1
    # print(line_id)
    # 无意义数值
    meaningless_value_1 = hex_list[8 + beats_num * 12:8 + beats_num * 12 + 2]
    # 谱面行数
    chart_num = int("".join(hex_list[10 + beats_num * 12:10 + beats_num * 12 + 2][::-1]), 16)
    # 无意义数值
    meaningless_value_2 = hex_list[12 + beats_num * 12:12 + beats_num * 12 + 2]
    # print(chart_num)

    parse_result = {"length": song_time, "bpm": beats_per_minute, "beat_num": beats_num, "chart_lines": chart_num, "notes": []}
    # print(hex_list)
    chart_start_index = 14 + beats_num * 12
    # 折线
    note_hex_l = {"0": None, "6": "start", "2": "mid", "A": "end"}
    # 普通键
    note_hex_r = {"0": "note", "1": "slide", "2": "hold"}
    line_id = 0
    for i, j in enumerate(hex_list[chart_start_index:]):
        if i % 11 == 0 and line_id < chart_num:
            # print(hex_list[i + chart_start_index:i + chart_start_index + 11])
            note_type_hex = "".join(hex_list[i + chart_start_index])
            poly_type = note_hex_l[note_type_hex[0]]
            note_type = note_hex_r[note_type_hex[1]]
            meaningless_value_3 = hex_list[i + chart_start_index + 1]
            note_time = int("".join(hex_list[i + chart_start_index + 2: i + chart_start_index + 5][::-1]), 16)
            start_track = hex_list[i + chart_start_index + 6]
            note_parameter_hex = "".join(hex_list[i + chart_start_index + 7:i + chart_start_index + 11])
            if note_type_hex[1] == "0" and note_parameter_hex == "00000000":
                note_parameter = 0
            elif note_type_hex[1] == "1":
                note_parameter = int("".join(reversed(hex_list[i + chart_start_index + 7:i + chart_start_index + 11])), 16)
                if note_parameter < 100:
                    note_parameter = note_parameter
                else:
                    note_parameter = -(4294967296 - note_parameter)
            elif note_type_hex[1] == "2":
                note_parameter = int("".join(reversed(hex_list[i + chart_start_index + 7:i + chart_start_index + 11])), 16)

            # print(poly_type, note_type, note_time, start_track, note_parameter)
            # print("\n")
            line_id = line_id + 1
            parse_result["notes"].append(
                {"id": line_id, "note_type": note_type, "note_time": note_time, "start_track": int(start_track), "note_parameter": note_parameter})
    return parse_result


def imd2aff(rm_path):
    hex_code = bin2hex(rm_path)
    rm_chart = parse(hex_code)

    afflist = []
    # 添加起始为0的小节线
    afflist.append(aff.Timing(0, rm_chart["bpm"]))
    # 添加符合延迟的小节线
    # afflist.append(aff.Timing(self.music.offset, self.music.bpm))
    for note in rm_chart["notes"]:
        note["used"] = False

    for note in rm_chart["notes"]:
        if note["note_type"] == "note":
            afflist.append(aff.Tap(note["note_time"], note["start_track"] + 1))
            note["used"] = True
        elif note["note_type"] == "hold" and not note["used"]:
            slide_hold = False
            connect = False
            for another_note in rm_chart["notes"]:
                if not connect:
                    if another_note["note_type"] == "slide" and another_note["note_time"] == note["note_time"] + note["note_parameter"] and not \
                            another_note["used"]:
                        slide_hold = True
                        x = 0.3333 * note["start_track"]
                        afflist.append(aff.Arc(note["note_time"], note["note_time"] + note["note_parameter"], x, x, 's', 1, 1, 0, False))
                        if another_note["note_parameter"] == 1:
                            afflist.append(
                                aff.Arc(note["note_time"] + note["note_parameter"], note["note_time"] + note["note_parameter"], x, x + 0.3333, 's', 1, 1,
                                        0, False))
                        elif another_note["note_parameter"] == 0:
                            afflist.append(
                                aff.Arc(note["note_time"] + note["note_parameter"], note["note_time"] + note["note_parameter"], x, x - 0.3333, 's', 1, 1,
                                        0, False))
                        another_note["used"] = True
                        connect = True

            if not slide_hold:
                afflist.append(aff.Hold(note["note_time"], note["note_time"] + note["note_parameter"], note["start_track"] + 1))
            note["used"] = True
        elif note["note_type"] == "slide" and not note["used"]:
            x = 0.3333 * note["start_track"]
            if note["note_parameter"] == 1:
                afflist.append(aff.Arc(note["note_time"], note["note_time"], x, x+0.3333, 's', 1, 1, 0, False))
            else:
                afflist.append(aff.Arc(note["note_time"], note["note_time"], x, x-0.3333, 's', 1, 1, 0, False))
            note["used"] = True

    continuous_arc = aff.Arc(0, 1, 0, 0, 's', 0, 0, 0, False)
    for i, o in enumerate(afflist):
        if type(o) == arcfutil.aff.Arc:
            same_start_arc = None
            for j, ex_o in enumerate(afflist):
                if not i == j and type(ex_o) == arcfutil.aff.Arc and o.time == ex_o.time \
                        and ((o.time == o.totime and ex_o.time == ex_o.totime) or (not o.time == o.totime and not ex_o.time == ex_o.totime)):
                    same_start_arc = True
                    if o.fromx > ex_o.fromx:
                        o.color = 1
                        ex_o.color = 0
                    else:
                        o.color = 0
                        ex_o.color = 1
            if not same_start_arc:
                if o.time == continuous_arc.totime and o.fromx == continuous_arc.tox and o.fromy == continuous_arc.toy:
                    o.color = continuous_arc.color
                else:
                    if o.fromx < 0.5:
                        o.color = 0
                    else:
                        o.color = 1
                continuous_arc = o
        # if type(o) == arcfutil.aff.Hold:
        #     if o.time == continuous_arc.totime:
        #         new_arc = continuous_arc
        #         new_arc.time = o.time
        #         new_arc.totime = o.totime
        #         new_arc.slideeasing = "si"
        #         afflist.remove(o)


    aff_obj = aff.AffList(afflist)
    aff.dumps(aff_obj, os.path.join(os.path.dirname(rm_path), "0.aff"))

    return afflist


def format_convert(input_file_path, target_format):
    print("[文件格式转换,目标格式：%s]" % target_format)
    output_format_path = os.path.join(os.path.dirname(input_file_path), "base.%s" % target_format)
    # ffmpeg_path = r"D:\LIFE\2022\Affcat\tool\ffmpeg.exe"
    cmd_console = "..\\tool\\ffmpeg.exe" + " -i %s %s" % (os.path.abspath(input_file_path), os.path.abspath(output_format_path))
    print(cmd_console)
    if not os.path.exists(input_file_path):
        print("-->未发现%s文件,转换中..." % target_format)
        try:
            print(cmd_console)
            os.system("cd tool")
            os.system(cmd_console)
        except Exception as e:
            print(e)
            print("-->格式转换失败")
            return False
    else:
        os.system(cmd_console)

    if not os.path.exists(output_format_path):
        print("-->格式转换失败")
    else:
        print("-->格式转换成功")

    return output_format_path


def note2format(notes):
    note_list = []
    for n in notes:
        # print(n)
        if n["note_type"] == "note":
            note_list.append({"note_type": "tap", "track": n["start_track"], "time": n["note_time"]})
        elif n["note_type"] == "hold":
            note_list.append(
                {"note_type": "hold", "track": n["start_track"], "time": n["note_time"], "end_time": n["note_time"] + n["note_parameter"]})
        elif n["note_type"] == "slide":
            note_list.append({"note_type": "slide", "track": n["start_track"], "direction": n["note_parameter"], "time": n["note_time"]})

    return note_list


def mp32ogg():
    data_path = "RhythmMaster"
    for song in os.listdir(data_path):
        chart_dir = os.path.join(data_path, song)
        if os.path.exists(os.path.join(chart_dir, "base.ogg")):
            continue
        else:
            for f in os.listdir(chart_dir):
                if f.endswith(".mp3"):
                    song_path = os.path.join(chart_dir, f)
                    format_convert(song_path, "ogg")


def save():
    data_path = "RhythmMaster"
    rm_4k = []
    part = 1
    for s_id, song in enumerate(os.listdir(data_path)):
        print("%d/%d" % (s_id, len(os.listdir(data_path))))
        try:
            chart_dir = os.path.join(data_path, song)
            # 每首歌曲建立一个索引
            new_song = {"song_id": chart_dir, "mode": "4K", "charts": []}
            for f in os.listdir(chart_dir):
                if f.endswith(".ogg"):
                    song_path = os.path.join(chart_dir, f)
                    new_song["song"] = librosa.load(song_path)
                if f.endswith(".imd"):
                    chart_path = os.path.join(chart_dir, f)
                    mode = f.split("_")[1]
                    if mode == "4k":
                        difficulty = f.split("_")[2]
                        hex_code = bin2hex(chart_path)
                        rm_chart = parse(hex_code)
                        note_format = note2format(rm_chart["notes"])
                        new_chart = {"bpm": rm_chart["bpm"], "difficulty": difficulty, "note": note_format, "offset": 0}
                        new_song["charts"].append(new_chart)

            rm_4k.append(new_song)

            if len(rm_4k) == 200:
                with open("rhythmMaster_4k_part%d.pickle" % part, "wb") as rm4k:
                    pickle.dump(rm_4k, rm4k)
                part += 1
                rm_4k = []
                print(part)

        except Exception as e:
            print(e)

    with open("rhythmMaster_4k_part%d.pickle" % part, "wb") as rm4k:
        pickle.dump(rm_4k, rm4k)


# mp32ogg()
imd2aff(rm_path=r"D:\LIFE\2022\Affcat\data\TEST\rm\canonrock\canonrock_4k_hd.imd")
# save()
# format_convert("chart/shisui.mp3", "ogg")
