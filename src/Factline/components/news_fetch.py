import requests
from bs4 import BeautifulSoup
from Factline.utils.helper import get_browser_headers,extract_article_content,get_topic_data
from Factline import logger
# To be shifted to YAML
# news_topics = ["india","india+politics", "global", "sports", "economic", "entertainment"]

class NewsData:
    def __init__(self,config, topic):
        self.config = config
        self.topic = topic
        
    def get_news_data(self):
        query = get_topic_data(self.topic)
        url = f"https://news.google.com/rss/search?q={query}"

        response = requests.get(url=url, headers=get_browser_headers())
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'xml')
        listnews = soup.find_all('item')[:3]
        if not listnews:
            logger.info("No news items found.")
            raise ValueError("No news items found")

        MAX_TOTAL_CHARS = 30000
        newslist = []
        total_chars = 0

        for i in listnews:
            title = i.find('title').text
            link = i.find('link').text

            content = extract_article_content(link)
            if not content:
                continue
            remaining = MAX_TOTAL_CHARS - total_chars

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


    

