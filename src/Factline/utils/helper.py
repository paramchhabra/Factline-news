from readability import Document
from googlenewsdecoder import gnewsdecoder
from bs4 import BeautifulSoup
import requests
from Factline.config.models import NewsQuery
from Factline.config.configuration import SystemPrompt, CHAT_MODEL
import yaml
from box import ConfigBox
from Factline import logger
import os
import yaml
from google.cloud import storage

CONFIG_PATH ="config/config.yaml"
STATE_PATH = "config/state.yaml"


def read_config():
    logger.info("Reading application configuration")

    try:
        with open(CONFIG_PATH, "r") as file:
            config = yaml.safe_load(file)

        return ConfigBox(config)

    except Exception as e:
        logger.exception("Failed to read application configuration: %s",e)
        raise

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
STATE_BLOB_NAME = "state.yaml"


def read_state():
    logger.info("Reading pipeline state from GCS")

    try:
        client = storage.Client()

        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(STATE_BLOB_NAME)

        state = yaml.safe_load(
            blob.download_as_text()
        )

        logger.info("Pipeline state loaded successfully")

        return state

    except Exception as e:
        logger.exception("Failed to read pipeline state from GCS: %s",e)
        raise

def write_state(index):

    client = storage.Client()

    try:    
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(STATE_BLOB_NAME)

        state = {
            "current_topic_index": index
        }

        blob.upload_from_string(
            yaml.safe_dump(state),
            content_type="application/x-yaml"
        )
    except Exception as e:
        logger.exception("Failed to write state with exception: %s",e)
        raise

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
        logger.exception("Failed to read content from url %s",url)
        return None

def get_topic_data(topic):
    try:
        url = f"https://news.google.com/rss/search?q=latest+{topic}+news"
        response = requests.get(url, headers=get_browser_headers(), timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'xml')
        listnews = soup.find_all('item')[:3]
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
    except Exception as e:
        logger.exception("Failed to get topic data with exception : %s",e)
        raise
