import requests
from bs4 import BeautifulSoup
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DB_FILE = "chat_history.db"

def fetch_news(keyword):
    url = f"https://news.google.com/rss/search?q={keyword}"
    # print("IN")
    # print(keyword)
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'lxml-xml')
        items = soup.find_all('item')[:5]
        # print("IN")
        # print(items)
        news_list = []
        for item in items:
            title = item.title.text
            content = item.description.text
            url = item.link.text
            news_list.append({"title": title})
        return news_list
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []

def check_news_relevance(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "system",
                "content": "You are a news analysis assistant. You need to determine if the user's input is asking about news-related content. If so, please extract keywords."
            }, {
                "role": "user",
                "content": "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            }],
            functions=[{
                "name": "analyze_news_query",
                "description": "Analyze if the user's input is news-related",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "is_news_related": {
                            "type": "boolean",
                            "description": "Whether it's news-related, this must be provided even if False"
                        },
                        "keywords": {
                            "type": "array",
                            "description": "Relevant news keywords",
                            "items": {
                                "type": "string"
                            }
                        }
                    }
                }
            }],
            function_call={"name": "analyze_news_query"}
        )

        result = json.loads(response.choices[0].message.function_call.arguments)
        return result
    except Exception as e:
        print(f"Error checking news relevance: {e}")
        return {"is_news_related": False, "keywords": []}