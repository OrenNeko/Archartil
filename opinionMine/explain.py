# 使用LLM对评论进行拓展解释

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

# 读取prompt\comment_explain.txt的内容，作为prompt_content
with open('prompt/comment_explain.txt', 'r', encoding='utf-8') as f:
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
            },
        ]
    )
    
    return completion.choices[0].message.content


# print(query_sentiment_analysis("有点像etr，这配置有点白开水了"))

if __name__ == "__main__":
    # 读取combined_comments.txt的内容，逐行进行情感分析
    comment_data = pd.read_csv('combined_comments_long.csv', encoding='utf-8')
    results = []
    error_comment = []
    for index, row in comment_data.iterrows():
        print(f"Processed comment {index + 1}/{len(comment_data)}")
        print(f"Comment: {row['comment']}")
        comment = row['comment']
        try:
            analysis_flag = True
            query_result = query_sentiment_analysis(comment)
            print(f"Raw response for comment {index + 1}: {query_result}")
        except Exception as e:
            print(f"Error processing comment {index + 1}: {e}")
            analysis_flag = False
            sentiment_result = {}
            error_comment.append({
                "source": row['source'],
                "difficulty": row['difficulty'],
                "comment": comment
            })
        if analysis_flag:    
            results.append({
                "source": row['source'],
                "difficulty": row['difficulty'],
                "comment": comment,
                "explain": query_result
            })
        else:
            results.append({
                "source": row['source'],
                "difficulty": row['difficulty'],
                "comment": comment,
                "explain": None
            })
            
        # 保存结果到explain_extend_results.csv
        results_df = pd.DataFrame(results)
        results_df.to_csv('explain_extend_results.csv', index=False, encoding='utf-8-sig')
        # 保存出错的评论error_comment到error_comments.csv
        error_df = pd.DataFrame(error_comment)
        error_df.to_csv('explain_error_comments.csv', index=False, encoding='utf-8-sig')
    
        