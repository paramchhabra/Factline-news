from readability import Document
from bs4 import BeautifulSoup
import requests
from Factline.config.configuration import SystemPrompt, CHAT_MODEL
import yaml
from box import ConfigBox
from Factline import logger
import os
import yaml
from google.cloud import storage
import json

CONFIG_PATH ="config/config.yaml"


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

def write_state(state):

    logger.info("Writing pipeline state to GCS")

    try:
        client = storage.Client()

        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(STATE_BLOB_NAME)

        blob.upload_from_string(
            yaml.safe_dump(state),
            content_type="application/x-yaml"
        )

        logger.info(
            "Pipeline state written successfully: %s",
            state
        )

    except Exception as e:
        logger.exception(
            "Failed to write pipeline state: %s",
            e
        )
        raise

def upload_artifact(data, local_path, blob_path):
    logger.info("Uploading artifact to GCS: %s", blob_path)

    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        if data is not None:
            if isinstance(data, bytes):
                with open(local_path, "wb") as file:
                    file.write(data)
            else:
                with open(local_path, "w") as file:
                    json.dump(
                        data.model_dump() if hasattr(data, "model_dump") else data,
                        file
                    )

        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_path)

        blob.upload_from_filename(local_path)

        logger.info(
            "Artifact uploaded successfully: %s",
            blob_path
        )

    except Exception as e:
        logger.exception(
            "Failed to upload artifact %s: %s",
            blob_path,
            e
        )
        raise


def download_artifact(blob_path, local_path):
    logger.info("Downloading artifact from GCS: %s", blob_path)

    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_path)

        blob.download_to_filename(local_path)

        if local_path.endswith(".json"):
            with open(local_path, "r") as file:
                return json.load(file)

        logger.info(
            "Artifact downloaded successfully: %s",
            blob_path
        )

        return local_path

    except Exception as e:
        logger.exception(
            "Failed to download artifact %s: %s",
            blob_path,
            e
        )
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
        response = requests.get(
            url,
            headers=get_browser_headers(),
            timeout=10
        )

        logger.info("Article status: %s", response.status_code)

        response.raise_for_status()

        doc = Document(response.text)
        summary_html = doc.summary()
        soup = BeautifulSoup(summary_html, "html.parser")
        text_only = soup.get_text(separator="\n", strip=True)

        return text_only

    except Exception as e:
        logger.exception(
            "Failed to read content with exception %s, from url %s",
            e,
            url
        )
        return None

def get_topic_data(topic):
    try:
        api_key = os.getenv("GNEWS_API_KEY")

        response = requests.get(
            "https://gnews.io/api/v4/search",
            params={
                "q": f"{topic} news",
                "lang": "en",
                "country": "in",
                "max": 10,
                "apikey": api_key
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        title_list = [
            article["title"]
            for article in data.get("articles", [])
        ][:3]

        if not title_list:
            raise RuntimeError(
                f"No news found for topic: {topic}"
            )

        response = CHAT_MODEL.invoke(
            [
                ("system", SystemPrompt.news_prompt(topic)),
                ("user", str(title_list))
            ]
        )

        return response.content

    except Exception as e:
        logger.exception(
            "Failed to get topic data with exception: %s",
            e
        )
        raise