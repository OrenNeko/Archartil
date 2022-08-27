import binascii
import struct


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
    beats_list = []
    line_id = 0
    for i, j in enumerate(hex_list[8:]):
        if i % 12 == 0 and line_id < beats_num:
            timestamp = int("".join(hex_list[i + 8:i + 12][::-1]), 16)
            beats_per_minute = struct.unpack('d', binascii.unhexlify("".join(hex_list[i + 12:i + 20])))[0]
            line_id = line_id + 1
    print(line_id)
    # 无意义数值
    meaningless_value_1 = hex_list[8 + beats_num * 12:8 + beats_num * 12 + 2]
    # 谱面行数
    chart_num = int("".join(hex_list[10 + beats_num * 12:10 + beats_num * 12 + 2][::-1]), 16)
    # 无意义数值
    meaningless_value_2 = hex_list[12 + beats_num * 12:12 + beats_num * 12 + 2]
    print(chart_num)

    chart_start_index = 25 + beats_num * 12
    note_hex_l = {"0": None, "6": "start", "2": "mid", "a": "end"}
    note_hex_r = {"0": "note", "1": "slide", "2": "hold"}
    line_id = 0
    for i, j in enumerate(hex_list[chart_start_index:]):
        if i % 11 == 0 and line_id < chart_num:
            print(hex_list[i + chart_start_index:i + chart_start_index + 11])
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
                if note_parameter_hex == "01000000":
                    note_parameter = 1
                elif note_parameter_hex == "FFFFFFFF":
                    note_parameter = -1
                else:
                    print("err")
            elif note_type_hex[1] == "2":
                note_parameter = int(note_parameter_hex[::-1], 16)
            print(poly_type, note_type, note_time, start_track, note_parameter)
            print("\n")
            line_id = line_id + 1
    return


b = bin2hex("chart/shisui_4k_ez.imd")
parse(b)
