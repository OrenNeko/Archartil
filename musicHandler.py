import os
import shutil
import librosa
import matplotlib.pyplot as plt
import librosa.display
import numpy as np


class MusicHandler:
    def __init__(self, music_parameter):
        """
        创建音乐工程
        :param project_path:
        :param sr:
        """
        if music_parameter["type"] == "file":
            self.file_path = music_parameter["file"]
            self.file_name = os.path.basename(self.file_path).split(".")[0]
            self.wav_path = os.path.splitext(music_parameter["file"])[0] + ".wav"
            if not os.path.exists(self.wav_path):
                self.format_convert("wav")
            self.sr = librosa.get_samplerate(self.wav_path)
            self.audio, self.sr = librosa.load(self.wav_path, sr=self.sr, offset=music_parameter["offset"])
            self.duration = librosa.get_duration(y=self.audio, sr=self.sr)
        elif music_parameter["type"] == "metric":
            # 调整延迟
            if music_parameter["offset"] > 0:
                self.audio = music_parameter["audio"][music_parameter["offset"]:]
            else:
                self.audio = np.pad(music_parameter["audio"], (-music_parameter["offset"], 0), 'constant', constant_values=(0, 0))
            self.sr = 44100
            self.duration = librosa.get_duration(y=self.audio, sr=self.sr)

        # self.get_bpm_and_offset()
        # print("-->音乐文件添加成功\nSampleRate:%s,Bpm:%s,Offset:%s." % (self.sr, self.bpm, self.offset))

    def format_convert(self, target_format):
        print("[文件格式转换,目标格式：%s]" % target_format)
        self.format_path = os.path.join(os.path.dirname(self.file_path), "base.%s" % target_format)
        cmd_console = "ffmpeg.exe -i %s %s" % (os.path.abspath(self.file_path), os.path.abspath(self.format_path))
        if not os.path.exists(self.format_path):
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

        if not os.path.exists(self.format_path):
            print("-->格式转换失败")
        else:
            print("-->格式转换成功")

    def get_bpm_and_offset(self):
        print("[BPM与OFFSET测定]")
        self.bpm, self.beats = librosa.beat.beat_track(y=self.audio, sr=self.sr)
        # self.bpm = round(self.bpm)

        while self.bpm < 100:
            self.bpm = round(self.bpm * 2)
        while self.bpm > 400:
            self.bpm = round(self.bpm / 2)
        self.onset = librosa.frames_to_time(frames=librosa.onset.onset_detect(y=self.audio), sr=self.sr) * 1000
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

    def plot_wave(self):
        plt.figure(figsize=(14, 5))
        plt.ylim(-5, 5)
        librosa.display.waveshow(self.audio, sr=self.sr)
        plt.show()

    def plot_frequency(self):
        X = librosa.stft(self.audio)
        Xdb = librosa.amplitude_to_db(abs(X))
        plt.figure(figsize=(14, 5))
        librosa.display.specshow(Xdb, sr=self.sr, x_axis='time', y_axis='hz')
        plt.colorbar()
        plt.show()

    def extract_feature(self, frame_interval=10):
        # PCG of Rhythm Games Using Deep Learning Methods
        # sr = 44100Hz, n_fft = 4096, window_size = 93ms, hop_length = 10ms

        # default window width, window_length = 4096 * 1000 / 44100 = 93ms
        n_fft = {"long": 4096, "middle": 2048, "short": 1024}
        # mel bands
        mel_bands = 80
        # forward and backward context N
        N = 7
        # mel max frequency
        mel_fmax = 16000
        # mel min frequency
        mel_fmin = 27.5

        stride = round(frame_interval * self.sr / 1000)
        frame_length = round(self.duration * 1000 / frame_interval)

        # Mel result
        Mel = {}
        for l in ["long", "middle", "short"]:
            S = librosa.stft(self.audio, n_fft=n_fft[l], hop_length=stride)
            Mel[l] = librosa.amplitude_to_db(np.real(librosa.feature.melspectrogram(S=S, sr=self.sr, n_mels=mel_bands, fmin=mel_fmin, fmax=mel_fmax)))

        # input frame feature
        frames_feature = []
        for frame_id in range(frame_length):
            frame_extend = []
            for extend_i in range(-N, N + 1):
                if 0 <= frame_id + extend_i < Mel[l].shape[1]:
                    frame_extend.append(
                        np.array([Mel["long"][:, frame_id + extend_i],
                                  Mel["middle"][:, frame_id + extend_i],
                                  Mel["short"][:, frame_id + extend_i]]).T)
                else:
                    frame_extend.append(np.array([np.zeros(80), np.zeros(80), np.zeros(80)]).T)
            frames_feature.append(frame_extend)

        frames_feature = np.array(frames_feature)

        return frames_feature


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
        print("-->%s声部检测完毕,端点音符数:%d" % (self.part, len(self.onset)))
