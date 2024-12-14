# Archartil-scoreView

因为官方的查分器太难用了就自己写了一个。

- 本工具仍需要通过官方API进行访问
- 未在非订阅账号上进行测试，所以目前不清楚无订阅账户是否可以爬取到个人的全部成绩
- 需要账号与密码换取Cookies（代码全部开源，可供安全检查）

### 使用方法

```
queryScore.py --account xxx@xxx.com --password xxx
```


输入账号密码后会向官网换取Cookies， 然后爬取得到``ptt_score.json``和``score.json``两个文件。

目录下需要有一份标准定数表``standard_rating.json``（可以在工具首页的``resources``下载）。

工具最后会生成一个``score.html``供预览查看。


可选参数：

- ``standard``:是否需要重新从wiki上爬取标准定数表。需要先完成成绩爬取，本地有包含全部歌曲的``score.json``，然后才会通过wiki抓定数表。因为定数表的曲名不为唯一的song_id，所以爬取后会完成一次比对，未爬取的本地会报错，建议选择资源文件中已经爬好的文件。


