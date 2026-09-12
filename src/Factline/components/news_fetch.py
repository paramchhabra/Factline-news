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

        newslist = []

        for i in listnews:
            title = i.find('title').text
            link = i.find('link').text
            content = extract_article_content(link)
            published_on = i.find('pubDate').text
            source = i.find('source').text if i.find('source') else "Unknown"

            newslist.append({
                "Title": title,
                "Content": content,
                "Published_On": published_on,
                "Source": source
            })
        logger.info("Data Provided")
        return str(newslist)


    

