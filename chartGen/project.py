import os.path
import random

from arcfutil import aff
from chartGen.genHandler.musicHandler import MusicHandler


class Project:
    def __init__(self, project_path):
        """
        :param project_path: 工程目录
        """
        self.project_path = project_path
        self.afflist = []

    def add_music(self, music_file, separate_stems):
        self.music = MusicHandler(music_file=music_file)
        self.music.reload(stems=separate_stems)

    def get_timestamps(self, timestamps_div=4, tolerance_times=1):
        """
        :param timestamps_div: 时间戳分度值，以小节分拍为单位，默认值为4，按四分采音
        :param tolerance_times: 可容忍最大距离，以时间戳增量为单位，默认值为1，为一个时间戳增量的长度,此值越大采音越多
        """
        print("[生成时间戳]")
        if not self.music:
            print("!Error:请添加音乐")
            return

        self.timestamps_div = timestamps_div
        self.tolerance_times = tolerance_times

        print("-->输入音频BPM:%d,输入音频偏置:%d,输入音频时长:%d,设定时间增量分度:%d]"
              % (self.music.bpm, self.music.offset, self.music.duration * 1000, self.timestamps_div))
        self.timestamps_delta = 60 * 1000 / self.music.bpm * (4 / self.timestamps_div)
        print("-->时间戳增量：", round(self.timestamps_delta))
        self.tolerance = round(self.timestamps_delta * self.tolerance_times)
        print("-->容忍误差最大范围：", self.tolerance)
        max_add_count = round(self.music.duration * 1000 / self.timestamps_delta)
        self.timestamps = [round(self.music.offset + i * self.timestamps_delta) for i in range(0, max_add_count)]
        print("-->共生成%d个时间戳，开始时间:%d，结束时间:%d。" % (max_add_count, self.timestamps[0], self.timestamps[-1]))

        # 添加起始为0的小节线
        self.afflist.append(aff.Timing(0, self.music.bpm))
        # 添加符合延迟的小节线
        self.afflist.append(aff.Timing(self.music.offset, self.music.bpm))

    def segment_fusion(self, weight):
        weight_sum = 0
        for w in weight:
            weight_sum += weight[w]
        for w in weight:
            weight[w] = weight[w] / weight_sum

        print("-->归一化权重:", weight)

        diff_part_onset_aligned = {}
        for dp in self.music.diff_parts:
            diff_part_onset_aligned[dp.part] = self.timestamps_align(base_ts=self.timestamps, input_ts=dp.onset)

        self.timestamps_fusion = []
        aligned_result = {}
        for t in self.timestamps:
            aligned_result[t] = 0
        for oa in diff_part_onset_aligned:
            if oa in weight:
                for timestamp in diff_part_onset_aligned[oa]:
                    aligned_result[timestamp] += weight[oa]

        for art in aligned_result:
            if aligned_result[art] >= 0.5:
                self.timestamps_fusion.append(art)

        print("-->融合完毕，共合并得到%d个有效时间戳" % (len(self.timestamps_fusion)))

    def generate_notes(self, last_side=random.randint(0, 1), overlap=False):
        """
        按交互生成4K谱面,不指定起手则随机起手
        """
        if last_side == 0:
            # 左起手
            last_lane = 1
        else:
            # 右起手
            last_lane = 4

        for t in self.timestamps_fusion:
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

            self.afflist.append(new_note)

    def timestamps_align(self, base_ts, input_ts):
        aligned_bts = []
        for bts in base_ts:
            for tts in input_ts:
                if abs(bts - tts) < self.tolerance and bts not in aligned_bts:
                    aligned_bts.append(bts)

        return aligned_bts

    def dumps(self, save_name):
        aff.dumps(aff.AffList(self.afflist), os.path.join(self.project_path, save_name))
