from readability import Document
from googlenewsdecoder import gnewsdecoder
from bs4 import BeautifulSoup
import requests
from Factline.config.models import NewsQuery
from Factline.config.configuration import SystemPrompt, CHAT_MODEL
import yaml
from box import ConfigBox

CONFIG_PATH ="config/config.yaml"
STATE_PATH = "config/state.yaml"


def read_config():
    with open(CONFIG_PATH, "r") as file:
        config = yaml.safe_load(file)

    return ConfigBox(config)


def read_state():
    with open(STATE_PATH, "r") as file:
        state = yaml.safe_load(file)

    return ConfigBox(state)


def write_state(state):
    with open(STATE_PATH, "w") as file:
        yaml.safe_dump(
            dict(state),
            file,
            sort_keys=False
        )

def get_browser_headers()->dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
    }
    return headers

def extract_article_content(url):
    try:
        newurl = gnewsdecoder(url, interval=10)
        decoded_url = newurl.get("decoded_url")

        if not decoded_url:
            raise ValueError("Decoded URL not found")

        response = requests.get(
            decoded_url,
            headers=get_browser_headers(),
            timeout=10
        )
        response.raise_for_status()

        doc = Document(response.text)
        summary_html = doc.summary()
        soup = BeautifulSoup(summary_html, "html.parser")
        text_only = soup.get_text(separator="\n", strip=True)

        return text_only

    except Exception as e:
        return None

def get_topic_data(topic):
    url = f"https://news.google.com/rss/search?q=latest+{topic}+news"
    response = requests.get(url, headers=get_browser_headers(), timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'xml')
    listnews = soup.find_all('item')[:5]
    title_list = [i.find('title').text for i in listnews]

    response = CHAT_MODEL.invoke([("system",SystemPrompt.news_prompt(topic)),("user",str(title_list))],response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "news_query",
            "strict": True,
            "schema": NewsQuery.model_json_schema()
        }
    })
    return NewsQuery.model_validate_json(response.content).query