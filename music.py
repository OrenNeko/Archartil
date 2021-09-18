import os
import random
import librosa
import matplotlib.pyplot as plt
import librosa.display


class Music:
    def __init__(self, project_path, sr):
        print("--创建工程--")
        print("当前工程目录：", project_path)
        self.project_path = project_path
        self.sr = sr
        self.ogg_path = os.path.join(project_path, "base.ogg")
        self.wav_path = os.path.join(project_path, "base.wav")

        if not os.path.exists(self.wav_path):
            print("未发现wav文件，ffpemg转换中...")
            os.system("ffmpeg.exe -i %s %s" % (self.ogg_path, self.wav_path))

    def load(self):
        print("--加载音乐--")
        print("采样率：%d" % self.sr)
        self.audio, self.sr = librosa.load(self.wav_path, sr=self.sr)

    def get_bpm(self):
        print("--BPM计算--")
        self.bpm, self.beats = librosa.beat.beat_track(self.audio, self.sr)
        while self.bpm < 100:
            print(">BPM小于100，扩大1倍<")
            self.bpm = round(self.bpm * 2)
        print("BPM:", self.bpm)

    def get_start(self):
        print("--计算音乐开始点--")
        self.onset_timestamps = librosa.frames_to_time(librosa.onset.onset_detect(self.audio), self.sr) * 1000
        self.offset = round(self.onset_timestamps[0])
        print("Offset:", self.offset)

    def get_timestamps(self):
        print("--生成时间戳--")
        self.timestamps_delta = 60 * 1000 / self.bpm / 4
        self.timestamps_delta_d4 = self.timestamps_delta * 4
        print("时间戳增量（16分）：", round(self.timestamps_delta))
        print("时间戳增量（4分）：", round(self.timestamps_delta_d4))
        max_add_count = round(self.onset_timestamps[-1] / self.timestamps_delta) + 64
        self.timestamps = [round(self.offset + i * self.timestamps_delta) for i in range(0, max_add_count)]
        self.timestamps_d4 = [round(self.offset + i * self.timestamps_delta_d4) for i in range(0, round(max_add_count / 4))]
        print("共生成%d个时间戳，开始时间：%d，结束时间：%d。" % (max_add_count, self.timestamps[0], self.timestamps[-1]))

    def onset_compare(self):
        print("--Onset对齐--")
        self.onset_timestamps_align = []
        for ts in self.timestamps:
            for ots in self.onset_timestamps:
                if abs(ts - ots) < self.timestamps_delta:
                    self.onset_timestamps_align.append(ts)

    def beats_compare(self):
        print("--Beats对齐--")
        self.beats_timestamps = librosa.frames_to_time(self.beats, self.sr) * 1000
        self.beats_timestamps_align = []
        for ts in self.timestamps_d4:
            for bts in self.beats_timestamps:
                if abs(ts - bts) < self.timestamps_delta:
                    self.beats_timestamps_align.append(ts)


class Aff:
    def __init__(self, bpm, offset):
        self.bpm = bpm
        self.offset = offset
        self.aff = "AudioOffset:%d\n-\ntiming(0,%.2f,4.00);\n" % (self.offset, self.bpm)
        self.objects = []

    def all_to_tap(self, tap_timestamps):
        print(">>>时间戳转为轨道随机的tap...")
        for o in tap_timestamps:
            new_tap = Tap(track=random.randint(1, 4), time=o - self.offset)
            self.add_object(new_tap)

    def beats_and_onset_to_tap(self, beats_timestamps, onset_timestamps):
        self.all_to_tap(beats_timestamps)
        for ots in onset_timestamps:
            if ots not in beats_timestamps:
                new_tap = Tap(track=random.randint(1, 4), time=ots - self.offset)
                self.add_object(new_tap)

        self.objects.sort(key=lambda x: x.start_time)

    def tap_diff_track(self):
        print(">>>连续同轨的tap乱序...")
        current_track = 0
        same_time = 0
        for o in self.objects:
            if current_track == o.track:
                same_time += 1
            else:
                same_time = 0

            if same_time > 2:
                o.track = track_diff(o.track)

            current_track = o.track

    def tap_to_hold(self, time_interval):
        print(">>>间隔较大的tap转为hold...")
        object_length = len(self.objects)
        for i in range(0, object_length - 1):
            object_before = self.objects[i]
            object_after = self.objects[i + 1]

            if object_after.start_time - object_before.start_time > time_interval * 1.5:
                self.objects[i] = Hold(track=random.randint(1, 4), start_time=object_before.start_time,
                                       end_time=object_before.start_time + time_interval)

    def add_object(self, insert_obj):
        if insert_obj.type == "tap":
            for exist_obj in self.objects:
                if exist_obj.type == "tap" and insert_obj.start_time == exist_obj.start_time:
                    return False
                if exist_obj.type == "hold" and exist_obj.track == insert_obj.track and \
                        exist_obj.start_time < insert_obj.start_time < exist_obj.end_time:
                    return False

        self.objects.append(insert_obj)
        return True

    def error_fix_hold(self):
        error = 0
        error = 0
        for i in range(0, len(self.objects)):
            if self.objects[i].type == "hold":
                hold = self.objects[i]
                for exist_obj in self.objects:
                    if hold.track == exist_obj.track:
                        if exist_obj.type == "hold" and (hold.start_time < exist_obj.start_time < hold.end_time or
                                                         hold.start_time < exist_obj.end_time < hold.end_time):
                            self.objects[i].track = track_diff(self.objects[i].track)
                            error += 1

        print(">>>hold问题修正,共%d处错误" % error)
        return error

    def error_fix_tap(self):
        error = 0
        for i in range(0, len(self.objects)):
            if self.objects[i].type == "tap":
                tap = self.objects[i]
                for exist_obj in self.objects:
                    if tap.track == exist_obj.track:
                        if exist_obj.type == "hold" and exist_obj.start_time < tap.start_time < exist_obj.end_time:
                            self.objects[i].track = track_diff(self.objects[i].track)
                            error += 1

        print(">>>tap问题修正,共%d处错误" % error)
        return error

    def random_hold_to_arc(self):
        print(">>>hold随机转换为arc")
        for i in range(0, len(self.objects)):
            if self.objects[i].type == "hold" and random.randint(0, 1):
                self.objects[i] = Arc(start_time=self.objects[i].start_time,
                                      end_time=self.objects[i].end_time,
                                      start_x=random.randint(0, 1),
                                      end_x=random.randint(0, 100) / 100,
                                      arc_type=random.choice(["s", "si", "so", "sisi", "siso", "sosi", "soso"]),
                                      start_y=1,
                                      end_y=random.randint(0, 100) / 100,
                                      color=random.randint(0, 1),
                                      param="none",
                                      black="false")

                self.objects[i].color = self.objects[i].start_x

    def to_aff(self):
        print(">>>转为aff文件,当前队列物件数：%d..." % len(self.objects))
        objects_type_dict = {"tap": 0, "hold": 0, "arc": 0}
        for o in self.objects:
            objects_type_dict[o.type] += 1
            self.aff = self.aff + o.get_aff() + "\n"
        print(">>>转换完毕，其中Tap:%d|Hold:%d|Arc:%d。" % (objects_type_dict["tap"], objects_type_dict["hold"], objects_type_dict["arc"]))


class Tap:
    def __init__(self, track, time):
        self.type = "tap"
        self.track = track
        self.start_time = time

    def get_aff(self):
        self.aff = "(%d,%d);" % (self.start_time, self.track)
        return self.aff


class Hold:
    def __init__(self, track, start_time, end_time):
        self.type = "hold"
        self.track = track
        self.start_time = start_time
        self.end_time = end_time

    def get_aff(self):
        self.aff = "hold(%d,%d,%d);" % (self.start_time, self.end_time, self.track)
        return self.aff


class Arc:
    # arc(1028,1371,0.25,0.25,s,0.00,0.00,0,none,true);
    def __init__(self, start_time, end_time, start_x, end_x, arc_type, start_y, end_y, color, param, black):
        self.type = "arc"
        self.start_time = start_time
        self.end_time = end_time
        self.start_x = start_x
        self.start_y = start_y
        self.arc_type = arc_type
        self.end_x = end_x
        self.end_y = end_y
        self.color = color
        self.param = param
        self.black = black

    def get_aff(self):
        self.aff = "arc(%d,%d,%.2f,%.2f,%s,%.2f,%.2f,%d,%s,%s);" \
                   % (self.start_time, self.end_time, self.start_x, self.end_x, self.arc_type, self.start_y, self.end_y, self.color, self.param,
                      self.black)
        return self.aff


def track_diff(track):
    new_track = track

    while new_track == track:
        new_track = random.randint(1, 4)

    # print("track:%d->%d" % (track, new_track))
    return new_track


if __name__ == '__main__':
    project_path = "chart/worldexecuteme"
    m = Music(project_path, 44100)
    m.load()
    m.get_bpm()
    m.get_start()
    a = Aff(m.bpm, m.offset)
    m.get_timestamps()
    m.onset_compare()
    m.beats_compare()
    a.beats_and_onset_to_tap(m.beats_timestamps_align, m.onset_timestamps_align)
    a.tap_diff_track()
    a.tap_to_hold(time_interval=m.timestamps_delta_d4)

    tap_error = 1
    hold_error = 1
    while tap_error + hold_error > 0:
        tap_error = a.error_fix_tap()
        hold_error = a.error_fix_hold()
    a.random_hold_to_arc()
    a.to_aff()

    with open(os.path.join(project_path, "3.aff"), "w", encoding="utf-8") as aff_file:
        aff_file.write(a.aff)
