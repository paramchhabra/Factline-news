import requests
from bs4 import BeautifulSoup
from Factline.utils.helper import get_browser_headers,extract_article_content,get_topic_data
from Factline import logger
# To be shifted to YAML
# news_topics = ["india","india+politics", "global", "sports", "economic", "entertainment"]

class NewsData:
    def __init__(self,config, topic,max_chars):
        self.config = config
        self.topic = topic
        self.max_chars = max_chars
        
    def get_news_data(self):
        try:
            query = get_topic_data(self.topic)
        except Exception as e:
            for i in range(3):
                logger.info("Topic Data retrieval Failed due to the following error: %s, retrying %d",e,i)
                try: 
                    query = get_topic_data(self.topic)
                    break
                except Exception as e:
                    logger.info("Attempt %d failed: %s", i + 1, e)
                    continue
            else:
                logger.exception("Topic Data retrieval Failed due to the following error: %s",e)

        try:
            url = f"https://news.google.com/rss/search?q={query}"

            response = requests.get(url=url, headers=get_browser_headers())
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'xml')
            listnews = soup.find_all('item')[:3]
            if not listnews:
                logger.info("No news items found.")
                raise ValueError("No news items found")

            mc = self.max_chars
            newslist = []
            total_chars = 0

            for i in listnews:
                title = i.find('title').text
                link = i.find('link').text

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
                    "Published_On": i.find('pubDate').text,
                    "Source": i.find('source').text if i.find('source') else "Unknown"
                })

                total_chars += len(content)

            logger.info("Data Provided")
            return str(newslist)
        except Exception as e:
            logger.exception("Failed to extract article content due to following error: %s",e)
            raise

        

