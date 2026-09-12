import datetime
import os

from box import ConfigBox

from Factline.components.news_fetch import NewsData
from Factline.components.script_generation import ScriptGen
from Factline.components.audio_generation import AudioGen
from Factline.components.image_generation import ImageGen
from Factline.components.video_generation import VideoGen
from Factline.components.upload import Upload

from Factline.utils.helper import read_config
from Factline import logger


class Pipeline:

    def __init__(self):

        # Load configuration
        self.config = read_config()

        # Generate unique session ID for this pipeline object
        self.session_id = datetime.datetime.now().strftime(
            "%y%m%d%H%M%S"
        )

    def fetch_news(self, topic):

        logger.info(
            f"Fetching news for topic: {topic}"
        )

        news_component = NewsData(
            self.config,
            topic
        )

        news_data = news_component.get_news_data()

        if not news_data:
            raise RuntimeError(
                "News fetching failed."
            )

        return news_data

    def generate_script(self, news_data, topic, language):

        logger.info(
            f"Generating {language} script for {topic}"
        )

        script_config = ConfigBox({
            "topic": topic,
            "language": language,
            "transcript": news_data
        })

        script_component = ScriptGen(
            script_config
        )

        script = script_component.news_script()

        if not script:
            raise RuntimeError(
                "Script generation failed."
            )

        return script

    def generate_audio(self, script, language):

        logger.info(
            f"Generating {language} audio"
        )

        audio_config = self.config.audio_model
        audio_config.instructions = script.mood
        audio_config.input = script.script

        audio_component = AudioGen(
            audio_config
        )

        audio_response = audio_component.generate_speech()

        if audio_response is None:
            raise RuntimeError(
                "Audio generation failed."
            )

        audio_path = (
            f"artifacts/audio/"
            f"{self.session_id}_{language.lower()}.mp3"
        )

        with open(audio_path, "wb") as audio_file:
            audio_file.write(
                audio_response.read()
            )

        return audio_path

    def generate_image(self, script, language):

        logger.info(
            f"Generating {language} image"
        )

        image_config = self.config.image_model
        image_config.prompt = script.prompt

        image_component = ImageGen(
            image_config
        )

        image_data = image_component.create_bg_img()

        if image_data is None:
            raise RuntimeError(
                "Image generation failed."
            )

        image_path = (
            f"artifacts/images/"
            f"{self.session_id}_{language.lower()}.png"
        )

        with open(image_path, "wb") as image_file:
            image_file.write(image_data)

        return image_path

    def generate_video(
        self,
        audio_path,
        image_path,
        language
    ):

        logger.info(
            f"Generating {language} video"
        )

        video_config = self.config.video_model

        video_config.audio = audio_path
        video_config.background_image = image_path
        video_config.logo_image = (
            "artifacts/images/logo.png"
        )

        video_component = VideoGen(
            video_config
        )

        video_path = video_component.create_video(
            f"{self.session_id}_{language.lower()}"
        )

        if not video_path:
            raise RuntimeError(
                "Video generation failed."
            )

        return video_path

    def upload_video(
        self,
        script,
        video_path,
        language
    ):

        logger.info(
            f"Uploading {language} video"
        )

        upload_component = Upload(
            self.config
        )

        video_data = {
            "video_title": script.video_title,
            "description": script.description,
            "tags": script.tags
        }

        video_id = upload_component.upload(
            video_data,
            video_path,
            language
        )

        if not video_id:
            raise RuntimeError(
                "Video upload failed."
            )

        return video_id
    def run_language(
        self,
        news_data,
        image_path,
        language
    ):

        script = self.generate_script(
            news_data,
            language
        )

        audio_path = self.generate_audio(
            script,
            language
        )

        video_path = self.generate_video(
            audio_path,
            image_path,
            language
        )

        video_id = self.upload_video(
            script,
            video_path,
            language
        )

        return video_id

    def run(self, topic):
        # One session for BOTH languages
        self.session_id = datetime.datetime.now().strftime(
            "%y%m%d%H%M%S"
        )

        # Fetch news ONCE
        news_data = self.fetch_news(topic)

        # Generate image ONCE
        image_path = self.generate_image(news_data)

        # English
        self.run_language(
            news_data,
            image_path,
            "English"
        )

        # Hindi
        self.run_language(
            news_data,
            image_path,
            "Hindi"
        )
