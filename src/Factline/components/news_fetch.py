import os
import requests
from Factline.utils.helper import extract_article_content, get_topic_data
from Factline import logger

class NewsData:
    def __init__(self, config, topic, max_chars):
        self.config = config
        self.topic = topic
        self.max_chars = max_chars
        
    def get_news_data(self):
        try:
            query = get_topic_data(self.topic)
        except Exception as e:
            for i in range(3):
                logger.info(
                    "Topic Data retrieval Failed due to the following error: %s, retrying %d",
                    e,
                    i
                )
                try:
                    query = get_topic_data(self.topic)
                    break
                except Exception as e:
                    logger.info("Attempt %d failed: %s", i + 1, e)
                    continue
            else:
                logger.exception(
                    "Topic Data retrieval Failed due to the following error: %s",
                    e
                )
                raise

        try:
            response = requests.get(
                "https://gnews.io/api/v4/search",
                params={
                    "q": query,
                    "lang": "en",
                    "country": "in",
                    "max": 10,
                    "sortby": "publishedAt",
                    "apikey": os.getenv("GNEWS_API_KEY")
                },
                timeout=10
            )

            response.raise_for_status()

            data = response.json()
            listnews = data.get("articles", [])

            if not listnews:
                logger.info("No news items found.")
                raise ValueError("No news items found")

            mc = self.max_chars
            newslist = []
            total_chars = 0

            for i in listnews:
                title = i.get("title", "")
                link = i.get("url", "")

                content = extract_article_content(link)

                if not content:
                    continue

                remaining = mc - total_chars

                if remaining <= 0:
                    break

                content = content[:remaining]

                newslist.append({
                    "Title": title,
                    "Content": content,
                    "Published_On": i.get("publishedAt", ""),
                    "Source": i.get("source", {}).get("name", "Unknown")
                })

                total_chars += len(content)

            logger.info("Data Provided")
            return newslist

        except Exception as e:
            logger.exception(
                "Failed to extract article content due to following error: %s",
                e
            )
            raise