# BMS文件格式文档：http://bm98.yaneu.com/bm98/bmsformat.html
# 扩充的格式文档：https://blog.csdn.net/teajs/article/details/20698733

import codecs
import os

import arcfutil.aff
import librosa


def parse(bms_lines):
    player_mode = {"1": "Single", "2": "Two", "3": "Double"}
    channel_mode = {"01": "BGM", "02": "Beat", "03": "Speed", "04": "BGA", "06": "Miss", "07": "Layer", "09": "Pause"}

    bms_to_aff_track_tap = {"11": 1, "12": 5, "13": 2, "14": 6, "15": 3, "16": 0, "18": 7, "19": 4}
    bms_to_aff_track_hold = {"51": 1, "52": 5, "53": 2, "54": 6, "55": 3, "56": 0, "58": 7, "59": 4}

    output = {"meta": {}, "note": []}
    for line in bms_lines:
        # 实际有含义的编码行
        if line[0] == "#":
            line_data = line.replace("\r\n", "").split(" ")
            if line_data[0] == "#PLAYER":
                output["meta"]["player"] = player_mode[line_data[1]]
            if line_data[0] == "#TITLE":
                output["meta"]["title"] = "".join(line_data[1:])
            if line_data[0] == "#ARTIST":
                output["meta"]["artist"] = "".join(line_data[1:])
            if line_data[0] == "#BPM":
                output["meta"]["bpm"] = float(line_data[1])
            if line_data[0] == "#PLAYERLEVEL":
                output["meta"]["level"] = line_data[1]
            if line_data[0] == "#RANK":
                output["meta"]["rank"] = line_data[1]

    channels = {}
    for line in bms_lines:
        #  通道行
        if ":" in line and line[6] == ":":
            line = line.replace("\r\n", "")
            channel_id = line[1:4]
            channel_type = line[4:6]
            channel_message = line[7:]
            channel_message_len = int(len(channel_message) / 2)
            # print(channel_id, channel_type, channel_message, channel_message_len)

            if channel_id not in channels:
                channels[channel_id] = {"id": channel_id,
                                        "bpm": output["meta"]["bpm"],
                                        "beat": 1,
                                        "duration": 60000 / output["meta"]["bpm"] * 4 * 1,
                                        "note": []}

            # 01:BGM, 02:Beat, 03:Speed(Bpm), 04:BGA, 06:Miss, 07:Layer, 09:Pause,
            # 11-19:Note for 1, 21-29:Note for 2, 51-59:Long for 1, 61-69:Long for 2

            if channel_type in ["01", "04", "06", "07", "09"]:
                continue
            elif channel_type == "02":
                channels[channel_id]["beat"] = float(channel_message)
                channels[channel_id]["duration"] = 60000 / channels[channel_id]["bpm"] * 4 * channels[channel_id]["beat"]
            elif channel_type == "03":
                channels[channel_id]["bpm"] = float(channel_message)
                channels[channel_id]["duration"] = 60000 / channels[channel_id]["bpm"] * 4 * channels[channel_id]["beat"]
            elif channel_type in bms_to_aff_track_tap:
                print("#", channel_id, channel_type, channel_message, channel_message_len)
                for i in range(channel_message_len):
                    # 每2位取1个值
                    if not channel_message[i * 2:i * 2 + 2] == "00":
                        # 如果有音
                        channels[channel_id]["note"].append({"note_type": "tap",
                                                             "track": bms_to_aff_track_tap[channel_type],
                                                             "player": int(channel_type[0]),
                                                             "position": i,
                                                             "length": channel_message_len})
            elif channel_type in bms_to_aff_track_hold:
                last_chip = ""
                last_id = 0
                for i in range(channel_message_len):
                    # 如果有音
                    if not channel_message[i * 2:i * 2 + 2] == "00":
                        if last_chip and channel_message[i * 2:i * 2 + 2] == last_chip:
                            channels[channel_id]["note"].append({"note_type": "hold",
                                                                 "track": bms_to_aff_track_hold[channel_type],
                                                                 "player": int(channel_type[0]) - 4,
                                                                 "position": last_id,
                                                                 "end_position": i,
                                                                 "length": channel_message_len})
                            last_chip = ""
                            last_id = i
                        else:
                            last_chip = channel_message[i * 2:i * 2 + 2]
                            last_id = i
    for c in channels:
        channels[c]["note_count"] = {"hold": 0, "tap": 0}
        for n in channels[c]["note"]:
            if n["note_type"] == "tap":
                channels[c]["note_count"]["tap"] += 1
            elif n["note_type"] == "hold":
                channels[c]["note_count"]["hold"] += 1

    channel_start_time = 0
    for c in channels:
        print(channels[c])
        if not channels[c]["beat"] == 1 or not channels[c]["bpm"] == output["meta"]["bpm"]:
            output["note"].append({"note_type": "bpm", "time": channel_start_time, "bpm": channels[c]["bpm"], "beat": channels[c]["beat"]})
        for n in channels[c]["note"]:
            note_time = channel_start_time + channels[c]["duration"] / n["length"] * n["position"]
            if n["note_type"] == "tap":
                output["note"].append({"note_type": "tap", "time": note_time, "track": n["track"], "player": n["player"]})
            elif n["note_type"] == "hold":
                end_time = channel_start_time + channels[c]["duration"] / n["length"] * n["end_position"]
                output["note"].append(
                    {"note_type": "hold", "time": note_time, "end_time": end_time, "track": n["track"], "player": n["player"]})
        channel_start_time = channel_start_time + channels[c]["duration"]
    print(output)
    return output


def bms2aff(bms_path, offset, player=1):
    # 中文编码utf-8，日文编码Shift_JIS
    bms_f = codecs.open(bms_path, "r", encoding="Shift_JIS")
    bms_data = parse(bms_f.readlines())
    print(bms_data["meta"])
    note_list = [arcfutil.aff.Timing(0, bms_data["meta"]["bpm"])]
    for n in bms_data["note"]:
        if n["note_type"] == "bpm":
            note_list.append(arcfutil.aff.Timing(n["time"], bpm=n["bpm"], bar=float(n["beat"])))
        elif n["note_type"] == "tap" and n["player"] == player:
            if 0 < n["track"] <= 4:
                note_list.append(arcfutil.aff.Tap(time=n["time"], lane=n["track"]))
            elif n["track"] == 0:
                x = 0.5
                y = 0.5
                note_list.append(
                    arcfutil.aff.Arc(time=n["time"], totime=n["time"] + 1, fromx=x, fromy=y, tox=x, toy=y, slideeasing="s", color=0, isskyline=True,
                                     skynote=[n["time"]]))
            else:
                x = (n["track"] - 5) * 0.5
                note_list.append(
                    arcfutil.aff.Arc(time=n["time"], totime=n["time"] + 1, fromx=x, fromy=1, tox=x, toy=1, slideeasing="s", color=0, isskyline=True,
                                     skynote=[n["time"]]))
        elif n["note_type"] == "hold" and n["player"] == player:
            if 0 < n["track"] <= 4:
                note_list.append(arcfutil.aff.Hold(time=n["time"], totime=n["end_time"], lane=n["track"]))
            elif n["track"] == 0:
                x = 0.5
                y = 0.5
                note_list.append(
                    arcfutil.aff.Arc(time=n["time"], totime=n["end_time"], fromx=x, fromy=y, tox=x, toy=y, slideeasing="s", color=3, isskyline=False))
            else:
                x = (n["track"] - 5) * 0.5
                if x == 0:
                    c = 1
                elif x == 1:
                    c = 2
                else:
                    c = 3
                note_list.append(
                    arcfutil.aff.Arc(time=n["time"], totime=n["end_time"], fromx=x, fromy=1, tox=x, toy=1, slideeasing="s", color=c, isskyline=False))

    aff_obj = arcfutil.aff.AffList(note_list)

    # aff_obj.offset = offset

    save_path = os.path.join(os.path.dirname(bms_path), "0.aff")
    save_path = os.path.join(r"D:\LIFE\2022\Affcat\data\TEST\bms", "0.aff")
    print(aff_obj, save_path)
    arcfutil.aff.dumps(aff_obj, save_path)


data_path = "Bms/[TeamUOUO]NewYorkBackRaise"
bms_file = "_SPA.bms"
bms_mp4 = "BGA.mp4"

audio, sr = librosa.load(r"D:\LIFE\2022\Affcat\data\TEST\bms\base.mp3", sr=44100)
onset = librosa.frames_to_time(frames=librosa.onset.onset_detect(y=audio), sr=44100) * 1000
offset = round(onset[0])
print(offset)

bms2aff(bms_path=os.path.join(data_path, bms_file), offset=offset)
