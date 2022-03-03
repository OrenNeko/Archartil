# About
AFFCAT是一个根据音乐自动生成Arcaea音乐游戏谱面的工具，目前该工具正在持续开发之中。  
该工具目前支持：  
* 4K谱面生成
* 图片/字符转黑线

# Dependency
```Bash
(python>=3.8)
conda install -c conda-forge ffmpeg libsndfile  
pip install arcutil librosa spleeter
```
# Quick Start
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


# Note
本工具属个人开发，目前工具效果还不是很好，如果您有好的建议，请联系952066338@qq.com。
另外本工具使用的测试用例音乐及谱面均来自Arcaea游戏本体，如有版权问题请及时通知本人下架。

