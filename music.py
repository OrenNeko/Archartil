import os
import shutil
import librosa


class Music:
    def __init__(self, music_file):
        """
        创建音乐工程
        :param project_path:
        :param sr:
        """
        print("[添加音乐文件]")
        self.file_path = music_file
        self.file_name = os.path.basename(self.file_path).split(".")[0]
        self.wav_path = self.format_convert("wav")
        self.sr = librosa.get_samplerate(self.wav_path)
        self.audio, self.sr = librosa.load(self.wav_path, sr=self.sr)
        self.duration = librosa.get_duration(self.audio, sr=self.sr)
        self.get_bpm_and_offset()
        print("-->音乐文件添加成功\nSampleRate:%s,Bpm:%s,Offset:%s." % (self.sr, self.bpm, self.offset))

    def format_convert(self, target_format):
        print("[文件格式转换,目标格式：%s]" % target_format)
        self.format_path = os.path.join(os.path.dirname(self.file_path), "base.%s" % target_format)
        if not os.path.exists(self.format_path):
            print("-->未发现%s文件,转换中..." % target_format)
            try:
                os.system("ffmpeg.exe -i %s %s" % (self.format_path, self.wav_path))
            except Exception as e:
                print(e)
                print("-->格式转换失败")
                return False

        print("-->格式转换成功")
        return self.format_path

    def get_bpm_and_offset(self):
        print("[BPM与OFFSET测定]")
        self.bpm, self.beats = librosa.beat.beat_track(y=self.audio, sr=self.sr)
        self.bpm = round(self.bpm)

        while self.bpm < 100:
            self.bpm = round(self.bpm * 2)
        while self.bpm > 400:
            self.bpm = round(self.bpm / 2)
        self.onset = librosa.frames_to_time(frames=librosa.onset.onset_detect(y=self.audio[0:5000]), sr=self.sr) * 1000
        self.offset = round(self.onset[0])

        # self.duration = librosa.get_duration(self.audio, self.sr) * 1000
        # print("Duration:", self.duration)

    def separate(self, stem_num):
        print("[Spleeter拆分音乐,拆分数量:%d]" % stem_num)
        # 5stems安装包可能下载有问题，需要手动下载解压后放在pretrianed_models目录下
        self.separate_save_dir = os.path.join(os.path.dirname(self.file_path), "spleeter_separate_%d" % stem_num)
        if not os.path.exists(self.separate_save_dir):
            os.mkdir(self.separate_save_dir)
            separate_cmd = "spleeter separate -o %s -p spleeter:%dstems %s" % (self.separate_save_dir, stem_num, self.file_path)
            os.system(separate_cmd)

    def reload(self, stems=2):
        """
        重加载音乐文件
        """
        self.separate(stem_num=stems)
        print("[重加载音乐，用于分声部检测]")
        self.diff_parts = []
        for dif_part in ["vocals", "accompaniment", "drums", "bass", "other", "piano"]:
            dir_part_path = os.path.join(self.separate_save_dir, self.file_name, dif_part + ".wav")
            if os.path.exists(dir_part_path):
                sepa_part = SeparatorPart(part=dif_part, path=dir_part_path, base_music=self)
                self.diff_parts.append(sepa_part)

        print("-->加载完毕，共加载%d个分声部文件" % len(self.diff_parts))


class SeparatorPart:
    def __init__(self, part, path, base_music):
        self.part = part
        self.path = path
        self.base_music = base_music
        self.sr = librosa.get_samplerate(self.path)
        self.audio, self.sr = librosa.load(self.path, sr=self.sr)

        self.onset_detect()

    def onset_detect(self):
        print("-->%s声部正在进行音符端点检测" % self.part)
        self.onset = librosa.frames_to_time(librosa.onset.onset_detect(self.audio), self.sr) * 1000
        print("-->%s声部检测完毕,端点音符数:%d" % (self.part,len(self.onset)))