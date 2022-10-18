from arcfutil import aff


class AffHandler:
    def __init__(self, aff_file):
        self.path = aff_file
        self.aff_object = aff.loads(self.path)
        self.offset = self.aff_object.offset

        self.to_list()
        self.get_bpm()

    def to_list(self):
        self.afflist = []
        for i in range(self.aff_object.__len__()):
            self.afflist.append(self.aff_object.__getitem__(i))

    def get_bpm(self):
        for obj in self.afflist:
            if type(obj) in [aff.Timing] and obj.time == 0:
                self.bpm = obj.bpm

    def get_onset_times(self):
        self.onset_times = []
        #  返回一个aff文件的采音后的时间序列
        for obj in self.afflist:
            if type(obj) in [aff.Tap, aff.Arc]:
                if obj.time not in self.onset_times:
                    self.onset_times.append(obj.time)
