import requests
import time
import json
import argparse
from tqdm import tqdm
from bs4 import BeautifulSoup
from colorama import Fore, Style

def print_error(*args):
    print(Fore.RED + " ".join(map(str, args)) + Style.RESET_ALL)

def print_info(*args):
    print(Fore.GREEN + " ".join(map(str, args)) + Style.RESET_ALL)

class reqLowiro:
    def __init__(self):
        self.cookies = {
            "ctrcode": "CN",
            "sid": "",
        }
        self.headers = {
            "Host": "webapi.lowiro.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "Windows",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "ttps://arcaea.lowiro.com",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://arcaea.lowiro.com/",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
            }
        self.url = "https://webapi.lowiro.com/"
    
    def auth(self, authData):
        authResponse = requests.post(self.url + "auth/login", headers=self.headers, cookies=self.cookies, data=json.dumps(authData))

        if authResponse.status_code == 200:
            print_info("Login success, cookies:", authResponse.cookies.get_dict())
            self.cookies.update(authResponse.cookies.get_dict())
        else:
            print_error("Login failed, content:", authResponse.text)
            return False
        
    def getRatingScores(self):
        print("Getting rating scores...")
        res = requests.get(self.url + "webapi/score/rating/me", headers=self.headers, cookies=self.cookies)
        
        try:
            json_content = json.loads(res.text)
        except json.JSONDecodeError as e:
            print_error("JSON format error.")
            json_content = {}
            
        with open('ptt_scores.json', 'w', encoding='utf-8') as f:
            json.dump(json_content, f, ensure_ascii=False, indent=4)
        
        print_info("Data has been saved to <ptt_scores.json>")
        
    def getAllScores(self):
        print("Getting all scores...")
        url_template = self.url + "webapi/score/song/me/all?difficulty={difficulty}&page={page}&sort=score&term="
        results = []
        for difficulty in [1, 2, 3]:
            if difficulty == 1:
                pages = 30
                difficulty_name = "Present"
            elif difficulty == 2:
                pages = 50
                difficulty_name = "Future/Eternal"
            else:
                pages = 10
                difficulty_name = "Beyond"
                
            for page in tqdm(range(pages), desc=f"{difficulty_name}"):
                time.sleep(0.5)
                url = url_template.format(difficulty=difficulty, page=page)
                response = requests.get(url, headers=self.headers, cookies=self.cookies)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        for score in data["value"]["scores"]:
                            results.append(score)
        
        with open('scores.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        print_info("Data has been saved to <scores.json>.")

class reqWiki:
    def __init__(self):
        self.url = "https://arcwiki.mcd.blue/"
    
    def getStandardRating(self):
        print("Getting standard rating...")
        response = requests.get(self.url + "%E5%AE%9A%E6%95%B0%E8%AF%A6%E8%A1%A8")
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        rating_list = []
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    song_name = cols[0].text.strip()
                    ratings = {
                        'pst': cols[1].text.strip(),
                        'prs': cols[2].text.strip(),
                        'ftr': cols[3].text.strip(),
                        'byd': cols[4].text.strip(),
                        'etr': cols[5].text.strip()
                    }
                    rating_list.append({'song_name': song_name, 'rating': ratings})
        
        with open('scores.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        standard_ratings = {}
        for rating in rating_list:
            standard_rating_name = None
            if rating["song_name"] == "Quon" and rating["rating"]["byd"] == "10.2":
                standard_rating_name = "quonwacca"
            elif rating["song_name"] == "Genesis" and rating["rating"]["ftr"] == "9.8":
                standard_rating_name = "genesischunithm"
            else:
                for score in data:
                    rating_name = rating['song_name'].lower().replace(' ', '')
                    score_name = score['title']['en'].lower().replace(' ', '')
                    if rating_name == score_name:
                        standard_rating_name = score["song_id"]
                        break
            
            if standard_rating_name:
                standard_ratings[standard_rating_name] = rating["rating"]
            else:
                print_error(f"Rating not found for {rating['song_name']}")

        with open('standard_rating.json', 'w', encoding='utf-8') as f:
            json.dump(standard_ratings, f, ensure_ascii=False, indent=4)


class genHTML:
    def __init__(self):
        self.rating_file = "standard_rating.json"
        self.scores_file = "scores.json"
        self.ptt_scores_file = "ptt_scores.json"
        self.html_content = ""
        self.difficulty_map = {
            0: 'PST',
            1: 'PRS',
            2: 'FTR',
            3: 'BYD',
            4: 'ETR'
        }
    
    def load_data(self):
        try:
            with open(self.rating_file, 'r', encoding='utf-8') as f:
                self.rating_data = json.load(f)

            with open(self.scores_file, 'r', encoding='utf-8') as f:
                self.scores_data = json.load(f)
                
            with open(self.ptt_scores_file, 'r', encoding='utf-8') as f:
                self.ptt_scores_data = json.load(f)
        except FileNotFoundError as e:
            print_error("No file found: " + str(e.filename))


    
    def calculate_rating(self, score, standard_rating):
        if score >= 10000000:
            return standard_rating + 2
        elif score >= 9800000:
            return standard_rating + 1 + (score - 9800000) / 200000
        else:
            return max(0, standard_rating + (score - 9500000) / 300000)
    
    def update_rating(self):
        for score in self.scores_data:
            standard_rating = self.rating_data[score['song_id']][self.difficulty_map[score['difficulty']].lower()]
            score["rating"] = self.calculate_rating(score['score'], float(standard_rating))
 
    
    def generate(self):
        best_rated_scores = sorted(self.scores_data, key=lambda x: x['rating'], reverse=True)[:50]
        recent_rated_scores = self.ptt_scores_data['value']['recent_rated_scores']
        recent_scores = sorted(self.scores_data, key=lambda x: x['time_played'], reverse=True)[:50]

        best_sum = sum(score['rating'] for score in best_rated_scores[0:30])
        recent_sum = sum(score['rating'] for score in recent_rated_scores[0:10])
        player_rating = (best_sum + recent_sum) / 40
        best_rating = best_sum / 30
        recent_rating = recent_sum / 10

        for score in recent_rated_scores:
            for data_score in self.scores_data:
                if score['song_id'] == data_score['song_id'] and score['difficulty'] == data_score['difficulty']:
                    score['yearly_play_count'] = data_score['yearly_play_count']
        
        # 创建HTML内容
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Scores</title>
            <link rel="stylesheet" href="https://unpkg.com/element-ui/lib/theme-chalk/index.css">
            <script src="https://unpkg.com/vue@2"></script>
            <script src="https://unpkg.com/element-ui/lib/index.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js"></script>
            <style>
                body {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    flex-direction: column;
                }
                .basic-info {
                    margin-bottom: 20px;
                    font-size: 14px;
                    justify-content: center;
                }
                .song-block {
                    width: 500px;
                    margin: 10px;
                    padding: 10px;
                    box-sizing: border-box;
                    font-size: 14px; 
                    text-align: left;
                    display: flex;
                    border-bottom: none;      
                    align-items: center;
                    height: 100%;      
                }
                .song-title {
                    font-weight: bold;
                }
                .song-image {
                    width: 100px;
                    height: 100px;
                    margin-right: 10px;
                    max-height: 100%;
                }
                .song-details {
                    flex-grow: 1;
                }
            </style>
        </head>
        <body>
        <div id="app">
            <el-divider>Basic Info</el-divider>
            <div class="basic-info"> Rating: {{ player_rating.toFixed(4) }} 丨 B30: {{ best_rating.toFixed(4) }} 丨 R10: {{ recent_rating.toFixed(4) }}</div>
            <div style="display: flex; justify-content: space-between;">
                <div id="chart-best" style="width: 300px; height: 300px;"></div>
                <div id="chart-recent" style="width: 300px; height: 300px;"></div>
            </div>
            <el-divider>Best Rated Scores</el-divider>
            <div v-for="(score, index) in bestRatedScores" :key="`${score.song_id}-best`" class="song-block">
                <img :src="`https://webassets.lowiro.com/${score.bg}.jpg`" :alt="score.title.en" class="song-image">
                <div class="song-details">
                    <div class="song-title">#{{index + 1}} [{{ difficultyMap[score.difficulty] }}] {{ score.title.en.toUpperCase() }}</div>
                    <div>Score: {{ score.score }}</div>
                    <div>Your Rating: {{ score.rating.toFixed(4) }}</div>
                    <div>Standard Rating: {{ getStandardRating(score) }}</div>
                    <div>Pure/Far/Lost: {{ score.perfect_count }}/{{ score.near_count }}/{{ score.miss_count }}</div>
                    <div>Last Time Played: {{ formatDate(score.time_played) }}</div>
                    <div>Year Count: {{ score.yearly_play_count }}</div>
                </div>
            </div>
            <el-divider>Recent Rated Scores</el-divider>
            <div v-for="(score, index) in recentRatedScores" :key="`${score.song_id}-recent-rated`" class="song-block">
                <img :src="`https://webassets.lowiro.com/${score.bg}.jpg`" :alt="score.title.en" class="song-image">
                <div class="song-details">
                    <div class="song-title">#{{ index + 1 }} [{{ difficultyMap[score.difficulty] }}] {{ score.title.en.toUpperCase() }}</div>
                    <div>Score: {{ score.score }}</div>
                    <div>Your Rating: {{ score.rating.toFixed(4) }}</div>
                    <div>Standard Rating: {{ getStandardRating(score) }}</div>
                    <div>Pure/Far/Lost: {{ score.perfect_count }}/{{ score.near_count }}/{{ score.miss_count }}</div>
                    <div>Last Time Played: {{ formatDate(score.time_played) }}</div>
                    <div>Year Count: {{ score.yearly_play_count }}</div>
                </div>
            </div>
            <el-divider>Recent Scores</el-divider>
            <div v-for="(score, index) in recentScores" :key="`${score.song_id}-${score.time_played}-recent`" class="song-block">
                <img :src="`https://webassets.lowiro.com/${score.bg}.jpg`" :alt="score.title.en" class="song-image">
                <div class="song-details">
                    <div class="song-title">#{{ index + 1 }} [{{ difficultyMap[score.difficulty] }}] {{ score.title.en.toUpperCase() }}</div>
                    <div>Score: {{ score.score }}</div>
                    <div>Your Rating: {{ score.rating.toFixed(4) }}</div>
                    <div>Standard Rating: {{ getStandardRating(score) }}</div>
                    <div>Pure/Far/Lost: {{ score.perfect_count }}/{{ score.near_count }}/{{ score.miss_count }}</div>
                    <div>Last Time Played: {{ formatDate(score.time_played) }}</div>
                    <div>Year Count: {{ score.yearly_play_count }}</div>
                </div>
            </div>
        </div>
        <script>
            new Vue({
                el: '#app',
                data: {
                    bestRatedScores: """ + json.dumps(best_rated_scores) + """,
                    recentRatedScores: """ + json.dumps(recent_rated_scores) + """,
                    recentScores: """ + json.dumps(recent_scores) + """,
                    standardRatings: """ + json.dumps(self.rating_data) + """,
                    player_rating: """ + str(player_rating) + """,
                    best_rating: """ + str(best_rating) + """,
                    recent_rating: """ + str(recent_rating) + """,
                    currentScores: """ + json.dumps(recent_scores) + """,
                    difficultyMap: {
                        0: 'PST',
                        1: 'PRS',
                        2: 'FTR',
                        3: 'BYD',
                        4: 'ETR'
                    }
                },
                mounted() {
                    this.initChart(id='chart-best', scores=this.bestRatedScores, chartTitle='Best 30 Rated Scores');
                    this.initChart(id='chart-recent', scores=this.recentScores, chartTitle='Recent 50 Scores');
                },
                methods: {
                    async initChart(id, scores, chartTitle) {
                        const chart = echarts.init(document.getElementById(id));
                        
                        const sortedScores = scores.slice().sort((a, b) => a.time_played - b.time_played);
                        const times = sortedScores.map(item => new Date(item.time_played).toLocaleDateString());
                        const ratings = sortedScores.map(item => item.rating);
                        
                        const option = {
                            title: {
                                text: chartTitle,
                                left: 'center',
                                textStyle: {
                                    fontSize: 14
                                }
                            },
                            tooltip: {
                                trigger: 'axis',
                                    formatter: (params) => {
                                        const item = sortedScores[params[0].dataIndex];
                                        return `
                                            Date: ${new Date(item.time_played).toLocaleDateString()}<br>
                                            Time: ${new Date(item.time_played).toLocaleTimeString()}<br>
                                            Rating: ${item.rating.toFixed(4)}<br>
                                            Score: ${item.score}<br>
                                            Song:  [${this.difficultyMap[item.difficulty]}] ${item.title.en}<br>
                                            Artist: ${item.artist}
                                        `;
                                    }
                            },
                            xAxis: {
                                type: 'category',
                                data: times
                            },
                            yAxis: {
                                type: 'value'
                            },
                            series: [{
                                data: ratings,
                                type: 'line',
                                smooth: true
                            }]
                        };
                        
                        try{
                            chart.setOption(option);
                        } catch (error) {
                            console.error('Error fetching or processing data:', error);
                        }
                    },
                    getStandardRating(score) {
                        const difficulty = this.difficultyMap[score.difficulty].toLowerCase();
                        const songName = score.song_id;
                        const standardRating = this.standardRatings[songName] ? this.standardRatings[songName][difficulty] : "N/A";
                        if (standardRating !== "N/A") {
                            const adjustedStandardRating = parseFloat(standardRating) + 2;
                            const ratingDiff = parseFloat(score.rating) - adjustedStandardRating;
                            return `${adjustedStandardRating.toFixed(4)} [${ratingDiff.toFixed(4)}]`;
                        }
                        return "N/A";
                    },
                    formatDate(timestamp) {
                        const date = new Date(timestamp);
                        return date.toISOString().split('T')[0];
                    }
                }
            });
        </script>
        </body>
        </html>
        """

        # 保存HTML文件
        with open('scores.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print_info("Saved to <scores.html>")
    
        
def main():
    parser = argparse.ArgumentParser(description="Arcaea Score Query")
    parser.add_argument('--account', type=str, help='User name/Email/User id')
    parser.add_argument('--password', type=str, help='Password')
    parser.add_argument('--standard', type=bool, help='Update standard rating')
    
    args = parser.parse_args()
    reqL = reqLowiro()
    
    # Auth and get cookies
    if args.account and args.password:
        authData = {
            "email": args.account,
            "password": args.password
        }
        reqL.auth(authData)
        reqL.getRatingScores()
        reqL.getAllScores()

    else:
        # Print help message
        print_error("Please provide account and password.")
        parser.print_help()
       
    
    if reqL.cookies.get("sid"):
        # Update standard rating
        if args.standard:
            reqW = reqWiki()
            reqW.getStandardRating()
        
        # Generate HTML
        gen = genHTML()
        gen.load_data()
        gen.update_rating()
        gen.generate()

  
    
if __name__ == "__main__":
    main()
