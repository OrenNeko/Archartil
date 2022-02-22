from project import Project

if __name__ == '__main__':
    p = Project("chart/bookmaker")
    p.add_music(music_file="chart/bookmaker/base.wav", separate_stems=5)
    p.get_timestamps(timestamps_div=16, tolerance_times=2)
    parts_weight = {
        "vocals": 1,
        "drums": 2,
        "bass": 0,
        "piano": 0,
        "other": 2
    }
    p.segment_fusion(weight=parts_weight)
    p.generate_notes()
    p.dumps("3.aff")
