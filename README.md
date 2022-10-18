# AFFCAT
Affcat是一个根据音乐自动生成Arcaea音乐游戏谱面的工具，目前该工具正在持续开发之中。  
该工具目前支持：  
* 4K谱面生成
* 图片/字符转黑线
  * tool.blackLinePlot
* 谱面转换（RM的imd文件，Malody的mc文件）
  * data.malody.mc2aff
  * data.rhythmmaster.imd2aff

# Dependency
```Bash
(python>=3.8)
conda install -c conda-forge ffmpeg libsndfile 
pip install arcutil==0.9.0 librosa==0.9.2

Model:
conda install scikit-learn=1.2.1 tensorflow=2.9.0
pip install matplotlib=3.6.1
```
# Quick Start（Not Update）
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

# Dataset

| MusicGame#Mode | SongNum  | ChartNum|  ActionType | Size | Update | 
| :----: | :----: | :----: | :----: | :----: | :----: |
| Arcaea| | |Tap, Hold, Arc | | 2022.10.13|
| Malody#4K | 776| | Tap, Hold | | 2022.10.13|
| RhythmMaster#4K| 560 | | Tap, Hold, Slide| | 2022.10.13|

# Evaluation
* TASK1-采音

  |  | Spleeter | C-LSTM |
  | ----   | ----   |----   |
  | Accuracy |
  
* TASK2-布键
  
  |  | 左右交互 | C-LSTM |
  | ----   | ----   |----   |
  | Accuracy |

# Update
* 2022/10/18
    * 数据集处理，包括RM和Malody的4K谱面以及Arcaea谱面
    * 使用C-LSTM模型训练生成采音模型(model/trainModel.py)
* 2022/08/27
    * 添加节奏大师谱面转aff功能
* 2022/02/15
    * 图片转黑线功能
* 2021/10/17
    * 更新采音策略，使用spleeter的旋律鼓点分离方法进行谱面识别，效果一般
* 2021/09/18
    * 初次提交，使用librosa自带的断点检测进行谱面识别

# Note
* 本工具仍在开发阶段，如果您有好的建议，请联系952066338@qq.com。  
* 本工具使用的测试用例音乐及谱面来自部分音乐游戏本体，如有版权问题，请通知本人下架。

# Thanks
* [arcfutil](https://docs.arcaea.icu/)
* [librosa](http://librosa.org/doc/latest/index.html)
* [MalodyBeatmapGenerator](https://github.com/nladuo/AI_beatmap_generator)
* [MalodyBeatmapGenerator(MirrOrangeVer.)](https://github.com/mirrorange/AI_beatmap_generator)

