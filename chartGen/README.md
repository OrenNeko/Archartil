# Archartil-chartGen

## Dependency
```Bash
(python>=3.8)
conda install -c conda-forge ffmpeg libsndfile 
pip install arcutil==0.9.0 librosa==0.9.2

Model:
conda install scikit-learn=1.2.1 tensorflow=2.9.0
pip install matplotlib=3.6.1
```
## Quick Start（Not Update）
```python    
# 创建工程，生成或保存文件的基础目录
p = Project("chart/bookmaker")
# 添加音乐并按类型拆分音部,详情见spleeter库首页
p.add_music(music_file="chart/bookmaker/base.wav", separate_stems=5)
# 基于加载音乐的的bpm和offset生成时间戳
p.get_timestamps(timestamps_div=16, tolerance_times=2)
# 设置采音权重
parts_weight = {
    "vocals": 1,
    "drums": 2,
    "bass": 0,
    "piano": 0,
    "other": 2
}
# 根据不同的权重进行片段融合
p.segment_fusion(weight=parts_weight)
# 按交互规则生成note
p.generate_notes()
# 保存游戏谱面
p.dumps("3.aff")
```

## Dataset

| MusicGame#Mode | SongNum  | ChartNum|  ActionType | Size | Update | 
| :----: | :----: | :----: | :----: | :----: | :----: |
| Arcaea| | |Tap, Hold, Arc | | 2022.10.13|
| Malody#4K | 776| | Tap, Hold | | 2022.10.13|
| RhythmMaster#4K| 560 | | Tap, Hold, Slide| | 2022.10.13|

## Evaluation
* TASK1-采音

  |  | Spleeter | C-LSTM |
  | ----   | ----   |----   |
  | Accuracy |
  
* TASK2-布键
  
  |  | 左右交互 | C-LSTM |
  | ----   | ----   |----   |
  | Accuracy |