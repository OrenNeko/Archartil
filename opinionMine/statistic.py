# -*- coding: utf-8 -*-

# 统计结果信息
import pandas as pd
import json
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 1. 统计分类数量，计算每种评论的占比数量
comment_data = pd.read_csv('csv/sentiment_analysis_results.csv', encoding='utf-8')
comment_category_counts = comment_data['commentType'].value_counts()
total_comments = len(comment_data)
comment_category_percentages = (comment_category_counts / total_comments) * 100
print("Comment Category Counts:")
print(comment_category_counts)
print("\nComment Category Percentages:")
print(comment_category_percentages)

# 统计每种类别下，高频出现的词语

core_words_by_category = {}
for index, row in comment_data.iterrows():
    comment_type = row['commentType']
    core_words_str = row['coreWords']
    try:
        core_words = list(eval(core_words_str))
    except:
        core_words = []
    
    if comment_type not in core_words_by_category:
        core_words_by_category[comment_type] = []
    
    for word in core_words:
        # 如果词语不包含中文,不计入统计
        if any('\u4e00' <= char <= '\u9fff' for char in word):
            core_words_by_category[comment_type].append(word)

# 计算每个类别下的高频词,生成词云图

for comment_type, words in core_words_by_category.items():
    word_counts = Counter(words)
    most_common_words = word_counts.most_common(20)
    print(f"\nComment Type: {comment_type}")
    print("Most Common Core Words:")
    for word, count in most_common_words:
        print(f"{word}: {count}")

    wordcloud = WordCloud(font_path='simhei.ttf', width=800, height=400, background_color='white').generate_from_frequencies(word_counts)
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f'类别<{comment_type}>下的词云图')
    plt.show()

    
# 2. 分析情绪色彩打分体系下,影响情绪分数的高频词

# 构建新的 DataFrame 用于分析
new_data = comment_data.copy()
new_data = new_data.rename(columns={'sentimentScore': 'score', 'coreWords': 'keywords'})
# 展开 coreWords 列 
new_data['keywords'] = new_data['keywords'].apply(eval)
df_exploded = new_data.explode('keywords')
df_exploded = df_exploded.dropna(subset=['keywords', 'score'])
df_exploded = df_exploded[df_exploded['keywords'].apply(lambda x: any('\u4e00' <= char <= '\u9fff' for char in x))]


for comment_type, words in core_words_by_category.items():
    # 统计情绪分数的平均值
    sentiment_scores = comment_data[comment_data['commentType'] == comment_type]['sentimentScore']
    average_score = sentiment_scores.mean()
    print(f"\nComment Type: {comment_type}, Average Sentiment Score: {average_score}")
    
    # 只分析当前类别的 df_exploded
    df_type = df_exploded[df_exploded['commentType'] == comment_type].copy()

    # 统计关键词的出现次数、均值、标准差
    stats = df_type.groupby('keywords')['score'].agg(['count', 'mean', 'std']).reset_index()

# 过滤低频词 (建议 >=2)
stats = stats[stats['count'] >= 5]

# 排序：找出影响最大的词
top_positive = stats.sort_values(by='mean', ascending=False).head(20)
top_negative = stats.sort_values(by='mean', ascending=True).head(20)
top_controversial = stats.sort_values(by='std', ascending=False).head(20)

print("--- 正向驱动词 ---")
print(top_positive)
print("\n--- 负向痛点词 ---")
print(top_negative)

# 可视化：蝴蝶图 (Tornado Chart)
plt.figure(figsize=(10, 6))
plot_data = pd.concat([top_positive, top_negative]).drop_duplicates('keywords')
plot_data = plot_data.sort_values(by='mean', ascending=False)
sns.barplot(x='mean', y='keywords', data=plot_data, palette='coolwarm')
plt.axvline(2.5, color='gray', linestyle='--') # 中线
plt.axhline(len(top_positive)-0.5, color='gray', linestyle='--') # 分割线

plt.title(f'不同关键词下的平均情绪分数 - {comment_type}')
plt.xlabel('平均情绪分数')
plt.ylabel('关键词')
plt.tight_layout()
plt.show()
    
# 只分析特定词语和情绪分数的关系
special_words = ['神谱', '好玩', '爽谱', '创新', '合理', '好听', '很爽', '契合', '挺好玩', '张力', '粪谱', '卡手', '逆天', '抽象', '白开水', '看不懂', '离谱', '幽默', '交互', '配置', '手感', '初见', '反手', '尾杀', '天键', '底力', '位移', '手序', '直角', '黑线', '双押', '地键', '出张', '换手', '物量', '多指', '排键', '拇指', '读谱', '正攻', '二见', '手指', '判定', '天地', '超界', '节奏', '采音', '慢速', '流速', '物量', '副歌', '曲师', '谱师', '魔王', '蛇', '虹弧', '双星', '红框', '手法', '定数']
print(len(df_exploded))
filtered = df_exploded[df_exploded['keywords'].isin(special_words)][['keywords', 'score']]
print(f"Filtered data for special words, total records: {len(filtered)}")
stats = filtered.groupby('keywords')['score'].agg(['count', 'mean', 'std']).reset_index()
print(f"Computed stats for special words, total unique words: {len(stats)}")
# stats = df_exploded[df_exploded['keywords'].isin(special_words)].groupby('keywords')['score'].agg(['count', 'mean', 'std']).reset_index()
# 排序：找出影响最大的词
top_stats = stats.sort_values(by='mean', ascending=False)
print("--- 特定词语与情绪分数关系 ---")
print(top_stats)
# 可视化：蝴蝶图 (Tornado Chart)
plt.figure(figsize=(10, 20))
sns.barplot(x='mean', y='keywords', data=top_stats, palette='coolwarm')
plt.axvline(2.5, color='gray', linestyle='--') # 中线
plt.title(f'特定关键词下的平均情绪分数')
plt.xlabel('平均情绪分数')
plt.ylabel('关键词')
plt.tight_layout()
plt.show()
# 整体平均分
overall_average_score = df_exploded['score'].mean()
print(f"Overall Average Sentiment Score: {overall_average_score}")

# 3.谱师分析

读取带有songlist的评论数据
comment_data_with_songlist = pd.read_csv('csv\combined_comments_with_songlist.csv', encoding='utf-8')

# 根据chart_designer, 统计sentimentScore的分布和coreWords的分布
designer_group = comment_data_with_songlist.groupby('chart_designer')
designer_stats = []
for designer, group in designer_group:
    avg_score = group['sentimentScore'].mean()
    std_score = group['sentimentScore'].std()
    total_comments = len(group)
    
    # 统计核心词汇
    all_core_words = []
    for core_words_str in group['coreWords']:
        try:
            core_words = list(eval(core_words_str))
        except:
            core_words = []
        for word in core_words:
            if any('\u4e00' <= char <= '\u9fff' for char in word):
                all_core_words.append(word)
    
    word_counts = Counter(all_core_words)
    most_common_words = word_counts.most_common(5)
    
    designer_stats.append({
        'designer': designer,
        'average_score': avg_score,
        "std_score": std_score,
        'total_comments': total_comments,
        'most_common_words': most_common_words
    })

# 输出结果
for stats in designer_stats:
    print(f"\n谱师: {stats['designer']}")
    print(f"平均情绪分数: {stats['average_score']:.2f}")
    print(f"情绪分数标准差: {stats['std_score']:.2f}")
    print(f"评论总数: {stats['total_comments']}")
    print("高频核心词汇:")
    for word, count in stats['most_common_words']:
        print(f"{word}: {count}")
        
# 条形图显示全部谱师分数
designer_stats_df = pd.DataFrame(designer_stats)
designer_stats_df = designer_stats_df.sort_values(by='average_score', ascending=False)

plt.figure(figsize=(12, 8))
sns.barplot(x='average_score', y='designer', data=designer_stats_df, palette='viridis')
plt.title('各谱师的平均情绪分数')
plt.xlabel('平均情绪分数')
plt.ylabel('谱师')
plt.tight_layout()
plt.show()

# 气泡图显示谱师的评论数量和平均分，标注谱师名称和评论数，放大气泡
# 气泡图，颜色区分谱师，气泡大小表示评论总数
plt.figure(figsize=(10, 6))
scatter = plt.scatter(
    designer_stats_df['total_comments'],
    designer_stats_df['average_score'],
    s=designer_stats_df['total_comments'] * 2,  # 气泡大小
    c=range(len(designer_stats_df)),            # 不同谱师不同颜色
    cmap='tab20',
    alpha=0.7
)

plt.xlabel('评论总数')
plt.ylabel('平均情绪分数')
plt.title('谱师评论情绪气泡图')

# 标注谱师，保留2位小数的分数，评论数
for i, row in designer_stats_df.iterrows():
    plt.text(
        row['total_comments'],  # x 坐标
        row['average_score'],   # y 坐标
        f"{row['designer']} \n({row['average_score']:.2f}, {row['total_comments']} )",  # 标注内容
        fontsize=8,
        ha='center',
        va='center'
    )

plt.colorbar(scatter, label='谱师编号')
plt.tight_layout()
plt.show()

# 4. 分析BPM对情绪分数的影响

# 读取带有songlist的评论数据
comment_data_with_songlist = pd.read_csv('csv/combined_comments_with_songlist.csv', encoding='utf-8')
# 根据bpm分组,计算不同bpm下的平均情绪分数
bpm_group = comment_data_with_songlist.groupby('bpm')
bpm_stats = bpm_group['sentimentScore'].agg(['mean', 'count']).reset_index()
bpm_stats = bpm_stats[bpm_stats['count'] >= 5]  # 过滤掉评论数少于5的bpm
bpm_stats = bpm_stats.sort_values(by='bpm')
# 可视化bpm与平均情绪分数的关系,气泡图,气泡大小表示评论数量
plt.figure(figsize=(10, 6))
scatter = plt.scatter(
    bpm_stats['bpm'],
    bpm_stats['mean'],
    s=bpm_stats['count']*0.25,  # 气泡大小
    c=bpm_stats['bpm'],        # 不同BPM不同颜色
    cmap='viridis',
    alpha=0.7
)
# plt.xscale('log')  # 设置x轴为对数刻度
plt.title('不同BPM下的平均情绪分数')
plt.xlabel('BPM')
plt.ylabel('平均情绪分数')
plt.tight_layout()
plt.show()

# 进阶尝试：将BPM分桶
bins = [0, 130, 170, 210, 500]
labels = ['Slow', 'Mid', 'Fast', 'Extreme']
comment_data_with_songlist['bpm_range'] = pd.cut(comment_data_with_songlist['bpm'], bins=bins, labels=labels)

# 观察不同区间的评论数量,平均分和标准差
bpm_range_group = comment_data_with_songlist.groupby('bpm_range')
bpm_range_stats = bpm_range_group['sentimentScore'].agg(['mean', 'std', 'count']).reset_index()
print("\n不同BPM区间与平均情绪分数关系:")
print(bpm_range_stats)

# 计算相关系数
correlation = bpm_stats['bpm'].corr(bpm_stats['mean'])
print(f"BPM与平均情绪分数的相关系数: {correlation:.4f}")

# 根据is_collaborative分组,计算平均情绪分数
collab_group = comment_data_with_songlist.groupby('is_collaborative')
collab_stats = collab_group['sentimentScore'].agg(['mean', 'std', 'count']).reset_index()
print("\n是否合作谱师与平均情绪分数关系:")
print(collab_stats)

# 计算相关系数
correlation = comment_data_with_songlist['is_collaborative'].corr(comment_data_with_songlist['sentimentScore'])
print(f"是否合作谱师与情绪分数的相关系数: {correlation:.4f}")

# 5. 分析播放量和情绪分数的关系
comment_data_with_songlist = pd.read_csv('csv/combined_comments_with_songlist.csv', encoding='utf-8')
view_count_group = comment_data_with_songlist.groupby('view_count')


# 对播放量进行分桶
bins = [0, 5000, 10000, 50000, 100000, 200000, 300000]
labels = ['0-5k', '5k-10k', '10k-50k', '50k-100k', '100k-200k', '200k-300k']
comment_data_with_songlist['view_count_range'] = pd.cut(comment_data_with_songlist['view_count'], bins=bins, labels=labels)
view_count_group = comment_data_with_songlist.groupby('view_count_range')

view_count_stats = view_count_group['sentimentScore'].agg(['mean', 'std', 'count']).reset_index()
print("\n播放量与平均情绪分数关系:")
print(view_count_stats)
# 绘制mean折线图,标注数据点
plt.figure(figsize=(10, 6))
sns.lineplot(x='view_count_range', y='mean', data=view_count_stats, marker='o')
for i, row in view_count_stats.iterrows():
    plt.text(
        i,
        row['mean'] + 0.005,
        f"{row['mean']:.2f}",
        fontsize=9,
        ha='center',
        va='bottom'
    )
plt.title('不同播放量区间下的平均情绪分数')
plt.xlabel('播放量区间')
plt.ylabel('平均情绪分数')
plt.tight_layout()
plt.show()


# 计算相关系数
correlation = comment_data_with_songlist['view_count'].corr(comment_data_with_songlist['sentimentScore'])
print(f"播放量与情绪分数的相关系数: {correlation:.4f}")

# 6. 分析版本号和情绪分数的关系

# 读入数据
comment_data_with_songlist = pd.read_csv('csv/combined_comments_with_songlist.csv', encoding='utf-8')

# 处理版本号（将字符串版本号转为元组，便于比较和排序）
def version_to_tuple(v):
    parts = str(v).split('.')
    major = int(parts[0])
    minor = int(parts[1]) if len(parts) > 1 else 0
    return (major, minor)

comment_data_with_songlist['version_tuple'] = comment_data_with_songlist['vesion_id'].apply(version_to_tuple)

# # 按版本号分组计算均值和方差
version_group = comment_data_with_songlist.groupby('version_tuple')
version_stats = version_group['sentimentScore'].agg(['mean', 'std', 'count']).reset_index()

# 只保留版本号在3.10到6.8之间的数据
lower = (3, 10)
upper = (6, 8)
mask = version_stats['version_tuple'].apply(lambda x: lower <= x <= upper)
filtered_stats = version_stats[mask]

# 输出评论数量随版本变化的趋势图
version_group = comment_data_with_songlist.groupby('version_tuple')
version_counts = version_group.size().reset_index(name='comment_count')
plt.figure(figsize=(10, 6))
plt.scatter(
    version_counts['version_tuple'].apply(lambda x: f"{x[0]}.{x[1]}"),
    version_counts['comment_count'],
    alpha=0.7
)
plt.title('不同版本号下的评论数量趋势')
plt.xlabel('版本号')
plt.ylabel('评论数量')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# 绘制图像
plt.figure(figsize=(10, 6))
x_labels = filtered_stats['version_tuple'].apply(lambda x: f"{x[0]}.{x[1]}")
plt.scatter(x_labels, filtered_stats['mean'], alpha=0.7)

# 标识最高点和最低点
max_idx = filtered_stats['mean'].idxmax()
min_idx = filtered_stats['mean'].idxmin()

max_version = x_labels[max_idx]
min_version = x_labels[min_idx]
max_value = filtered_stats['mean'][max_idx]
min_value = filtered_stats['mean'][min_idx]
max_count = filtered_stats['count'][max_idx]
min_count = filtered_stats['count'][min_idx]

plt.scatter(max_version, max_value, color='red', label='最高点')
plt.scatter(min_version, min_value, color='blue', label='最低点')

# 标注版本号、均值和评论数量
plt.annotate(f'最高点\n版本号: {max_version}\n均值: {max_value:.2f}\n评论数: {max_count}',
             (max_version, max_value),
             xytext=(0, -50),
             textcoords='offset points',
             ha='center',
             color='red',
             fontsize=10,
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", lw=1))

plt.annotate(f'最低点\n版本号: {min_version}\n均值: {min_value:.2f}\n评论数: {min_count}',
             (min_version, min_value),
             xytext=(0, 20),
             textcoords='offset points',
             ha='center',
             color='blue',
             fontsize=10,
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="blue", lw=1))

plt.xlabel('版本号')
plt.ylabel('平均情绪分数')
plt.title('版本号3.10到6.8下的平均情绪分数')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()

# 输出4.5版本的每首曲目评价分布情况
special_version = 4.5
special_group = comment_data_with_songlist[comment_data_with_songlist['vesion_id'] == special_version]
song_grouped = special_group.groupby('source')
for song_name, group in song_grouped:
    score_counts = group['sentimentScore'].value_counts().sort_index()
    average_score = group['sentimentScore'].mean()
    std_score = group['sentimentScore'].std()
    print(f"\n曲目: {song_name}")
    print(f"评论数量: {len(group)}")
    print(f"平均情绪分数: {average_score:.2f}")
    print(f"情绪分数标准差: {std_score:.2f}")

# 7.分析特定曲目的评价分布情况
# 读入数据
comment_data_with_songlist = pd.read_csv('csv/combined_comments_with_songlist.csv', encoding='utf-8')

# 提取difficulty字符串序列中的数字,将大于11的确定为高难曲目
high_difficulty_songs = comment_data_with_songlist[comment_data_with_songlist['difficulty'].str.contains('11|12', na=False)]['source'].unique().tolist()

for song in high_difficulty_songs:
    special_group = comment_data_with_songlist[comment_data_with_songlist['source'].str.lower() == song]
    score_counts = special_group['sentimentScore'].value_counts().sort_index()
    # 分析均值,标准差
    average_score = special_group['sentimentScore'].mean()
    std_score = special_group['sentimentScore'].std()
    print(f"\n曲目: {song}")
    print(f"评论数量: {len(special_group)}")
    print(f"平均情绪分数: {average_score:.2f}")
    print(f"情绪分数标准差: {std_score:.2f}")


special_songs = ["alterego", "lamentrain", "designant"]
# 对特殊曲目,根据难度不同,输出相关分析数据
for song in special_songs:
    # 生成special_group时,不同难度分开
    special_group = comment_data_with_songlist[comment_data_with_songlist['source'].str.lower() == song]
    difficulty_grouped = special_group.groupby('difficulty')
    for difficulty, group in difficulty_grouped:
        score_counts = group['sentimentScore'].value_counts().sort_index()
        average_score = group['sentimentScore'].mean()
        std_score = group['sentimentScore'].std()
        print(f"\n曲目: {song}, 难度: {difficulty}")
        print(f"评论数量: {len(group)}")
        print(f"平均情绪分数: {average_score:.2f}")
        print(f"情绪分数标准差: {std_score:.2f}")
    