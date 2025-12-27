# 使用LLM对评论进行情感分析

from openai import OpenAI
import httpx
import pandas as pd
import json

client = OpenAI(
    base_url="", 
    api_key="",
    http_client=httpx.Client(
        base_url="",
        follow_redirects=True,
    ),
)


# 读取prompt\sentiment_analysis.txt的内容，作为prompt_content
with open('prompt/sentiment_analysis.txt', 'r', encoding='utf-8') as f:
    prompt_content = f.read()


def query_sentiment_analysis(comment):
    completion = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system", 
                "content": prompt_content
            },
            {
                "role": "user", 
                "content": comment
            }
        ]
    )
    
    return completion.choices[0].message.content

if __name__ == "__main__":
    # 读取combined_comments.txt的内容，逐行进行情感分析
    comment_data = pd.read_csv('csv/explain_extend_results.csv', encoding='utf-8')
    results = []
    error_comment = []
    for index, row in comment_data.iterrows():
        print(f"Processed comment {index + 1}/{len(comment_data)}")
        print(f"Comment: {row['comment']}")
        print(f"Explanation: {row['explain']}")
        extend_comment = "用户评论:" + row['comment'] + "\n" + "评论解释:" + row['explain']
        try:
            analysis_flag = True
            query_result = query_sentiment_analysis(extend_comment)
            print(f"Raw response for comment {index + 1}: {query_result}")
            sentiment_result = json.loads(query_result)
            commentType = sentiment_result["commentType"]
            sentimentScore = sentiment_result["sentimentScore"]
            coreWords = sentiment_result["coreWords"]
        except Exception as e:
            print(f"Error processing comment {index + 1}: {e}")
            analysis_flag = False
            sentiment_result = {}
            error_comment.append({
                "source": row['source'],
                "difficulty": row['difficulty'],
                "comment": row['comment'],
                "explain": row['explain']
            })
        if analysis_flag:    
            results.append({
                "source": row['source'],
                "difficulty": row['difficulty'],
                "comment": row['comment'],
                "explain": row['explain'],
                "commentType": commentType,
                "sentimentScore": sentimentScore,
                "coreWords": coreWords
            })
        else:
            results.append({
                "source": row['source'],
                "difficulty": row['difficulty'],
                "comment": row['comment'],
                "explain": row['explain'],
                "commentType": None,
                "sentimentScore": None,
                "coreWords": None
            })
            
        # 保存结果到sentiment_analysis_results.csv
        results_df = pd.DataFrame(results)
        results_df.to_csv('csv/sentiment_analysis_results.csv', index=False, encoding='utf-8-sig')
        # 保存出错的评论error_comment到error_comments.csv
        error_df = pd.DataFrame(error_comment)
        error_df.to_csv('csv/sentiment_error_comments.csv', index=False, encoding='utf-8-sig')
    
        