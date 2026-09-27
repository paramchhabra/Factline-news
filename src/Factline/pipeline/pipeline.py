import datetime
import os
import json
from box import ConfigBox
from Factline.components.news_fetch import NewsData
from Factline.components.script_generation import ScriptGen
from Factline.components.audio_generation import AudioGen
from Factline.components.image_generation import ImageGen
from Factline.components.video_generation import VideoGen
from Factline.components.upload import Upload
from Factline.utils.helper import read_config,upload_artifact,download_artifact,write_state
from Factline import logger


class Pipeline:

    MAX_RETRIES = 3

    def __init__(self):

        self.config = read_config()

    def retry_operation(self, operation, operation_name):

        for attempt in range(1, self.MAX_RETRIES + 1):

            try:
                return operation()

            except Exception:

                logger.exception(
                    "%s failed. Attempt %d/%d",
                    operation_name,
                    attempt,
                    self.MAX_RETRIES
                )

                if attempt == self.MAX_RETRIES:
                    raise
      
    def fetch_news(self, topic):
        logger.info(f"Fetching news for topic: {topic}")

        max_chars = self.config.max_chars

        for attempt in range(1, 4):
            try:
                logger.info(
                    "Fetching news with max_chars=%d. Attempt %d/3",
                    max_chars,
                    attempt
                )

                news_component = NewsData(
                    self.config,
                    topic,
                    max_chars
                )

                news_data = news_component.get_news_data()

                if not news_data:
                    raise RuntimeError("News fetching failed.")

                return news_data

            except Exception:
                logger.exception(
                    "News fetching failed with max_chars=%d",
                    max_chars
                )

                if attempt == 3:
                    raise

                max_chars -= 10000

                if max_chars <= 0:
                    raise RuntimeError(
                        "News fetching failed after reducing max_chars."
                    )
                
    def generate_script(self, news_data, topic, language):

        logger.info(
            f"Generating {language} script for {topic}"
        )

        script_config = ConfigBox({
            "topic": topic,
            "language": language,
            "transcript": str(news_data)[:22000]
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

    def generate_image(self, script):

        logger.info(
            "Generating image"
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
            f"{self.session_id}.png"
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
        video_config.logo_image = "logo.png"

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

    def run(self, topic, state):
        self.session_id = state.get("session_id")

        if not self.session_id:
            self.session_id = datetime.datetime.now().strftime("%y%m%d%H%M%S")
            state["session_id"] = self.session_id

        stage = state.get("stage")

        stage_order = [
            "news",
            "english_script",
            "english_audio",
            "image",
            "english_video",
            "english_upload",
            "hindi_script",
            "hindi_audio",
            "hindi_video",
            "hindi_upload"
        ]

        if stage and stage != "complete":
            completed_stages = stage_order[:stage_order.index(stage) + 1]
        else:
            completed_stages = []

        logger.info(
            "Starting pipeline | topic=%s | session_id=%s | stage=%s",
            topic,
            self.session_id,
            stage
        )

        if "news" not in completed_stages:
            logger.info("News stage not completed. Fetching news.")

            news_data = self.fetch_news(topic)

            news_path = f"artifacts/{self.session_id}_news.json"

            self.retry_operation(
                lambda: upload_artifact(
                    news_data,
                    news_path,
                    f"runs/{self.session_id}/news.json"
                ),
                "Uploading news artifact"
            )

            state["stage"] = "news"
            completed_stages.append("news")
            write_state(state)

        else:
            logger.info("News already completed. Loading news.")

            news_path = f"artifacts/{self.session_id}_news.json"

            news_data = self.retry_operation(
                lambda: download_artifact(
                    f"runs/{self.session_id}/news.json",
                    news_path
                ),
                "Downloading news artifact"
            )

        if "english_script" not in completed_stages:
            logger.info("English script not completed. Generating script.")

            script = self.retry_operation(
                lambda: self.generate_script(
                    news_data,
                    topic,
                    "English"
                ),
                "English script generation"
            )

            script_path = f"artifacts/{self.session_id}_english_script.json"

            self.retry_operation(
                lambda: upload_artifact(
                    dict(script),
                    script_path,
                    f"runs/{self.session_id}/english/script.json"
                ),
                "Uploading English script"
            )

            state["stage"] = "english_script"
            completed_stages.append("english_script")
            write_state(state)

        else:
            logger.info("English script already completed. Loading script.")

            script_path = f"artifacts/{self.session_id}_english_script.json"

            script = ConfigBox(
                self.retry_operation(
                    lambda: download_artifact(
                        f"runs/{self.session_id}/english/script.json",
                        script_path
                    ),
                    "Downloading English script"
                )
            )

        if "english_audio" not in completed_stages:
            logger.info("English audio not completed. Generating audio.")

            audio_path = self.retry_operation(
                lambda: self.generate_audio(
                    script,
                    "English"
                ),
                "English audio generation"
            )

            self.retry_operation(
                lambda: upload_artifact(
                    None,
                    audio_path,
                    f"runs/{self.session_id}/english/audio.mp3"
                ),
                "Uploading English audio"
            )

            state["stage"] = "english_audio"
            completed_stages.append("english_audio")
            write_state(state)

        else:
            logger.info("English audio already completed. Downloading audio.")

            audio_path = f"artifacts/audio/{self.session_id}_english.mp3"

            self.retry_operation(
                lambda: download_artifact(
                    f"runs/{self.session_id}/english/audio.mp3",
                    audio_path
                ),
                "Downloading English audio"
            )

        if "image" not in completed_stages:
            logger.info("Image not completed. Generating image.")

            image_path = self.retry_operation(
                lambda: self.generate_image(script),
                "Image generation"
            )

            self.retry_operation(
                lambda: upload_artifact(
                    None,
                    image_path,
                    f"runs/{self.session_id}/english/image.png"
                ),
                "Uploading image"
            )

            state["stage"] = "image"
            completed_stages.append("image")
            write_state(state)

        else:
            logger.info("Image already completed. Downloading image.")

            image_path = f"artifacts/images/{self.session_id}.png"

            self.retry_operation(
                lambda: download_artifact(
                    f"runs/{self.session_id}/english/image.png",
                    image_path
                ),
                "Downloading image"
            )

        if "english_video" not in completed_stages:
            logger.info("English video not completed. Generating video.")

            video_path = self.retry_operation(
                lambda: self.generate_video(
                    audio_path,
                    image_path,
                    "English"
                ),
                "English video generation"
            )

            self.retry_operation(
                lambda: upload_artifact(
                    None,
                    video_path,
                    f"runs/{self.session_id}/english/video.mp4"
                ),
                "Uploading English video"
            )

            state["stage"] = "english_video"
            completed_stages.append("english_video")
            write_state(state)

        else:
            logger.info("English video already completed. Downloading video.")

            video_path = f"artifacts/videos/{self.session_id}_english.mp4"

            self.retry_operation(
                lambda: download_artifact(
                    f"runs/{self.session_id}/english/video.mp4",
                    video_path
                ),
                "Downloading English video"
            )

        if "english_upload" not in completed_stages:
            logger.info("English video not uploaded. Uploading.")

            self.retry_operation(
                lambda: self.upload_video(
                    script,
                    video_path,
                    "English"
                ),
                "English video upload"
            )

            state["stage"] = "english_upload"
            completed_stages.append("english_upload")
            write_state(state)

        else:
            logger.info("English video already uploaded.")

        if "hindi_script" not in completed_stages:
            logger.info("Hindi script not completed. Generating script.")

            hindi_script = self.retry_operation(
                lambda: self.generate_script(
                    news_data,
                    topic,
                    "Hindi"
                ),
                "Hindi script generation"
            )

            hindi_script_path = f"artifacts/{self.session_id}_hindi_script.json"

            self.retry_operation(
                lambda: upload_artifact(
                    dict(hindi_script),
                    hindi_script_path,
                    f"runs/{self.session_id}/hindi/script.json"
                ),
                "Uploading Hindi script"
            )

            state["stage"] = "hindi_script"
            completed_stages.append("hindi_script")
            write_state(state)

        else:
            logger.info("Hindi script already completed. Loading script.")

            hindi_script_path = f"artifacts/{self.session_id}_hindi_script.json"

            hindi_script = ConfigBox(
                self.retry_operation(
                    lambda: download_artifact(
                        f"runs/{self.session_id}/hindi/script.json",
                        hindi_script_path
                    ),
                    "Downloading Hindi script"
                )
            )

        if "hindi_audio" not in completed_stages:
            logger.info("Hindi audio not completed. Generating audio.")

            hindi_audio_path = self.retry_operation(
                lambda: self.generate_audio(
                    hindi_script,
                    "Hindi"
                ),
                "Hindi audio generation"
            )

            self.retry_operation(
                lambda: upload_artifact(
                    None,
                    hindi_audio_path,
                    f"runs/{self.session_id}/hindi/audio.mp3"
                ),
                "Uploading Hindi audio"
            )

            state["stage"] = "hindi_audio"
            completed_stages.append("hindi_audio")
            write_state(state)

        else:
            logger.info("Hindi audio already completed. Downloading audio.")

            hindi_audio_path = f"artifacts/audio/{self.session_id}_hindi.mp3"

            self.retry_operation(
                lambda: download_artifact(
                    f"runs/{self.session_id}/hindi/audio.mp3",
                    hindi_audio_path
                ),
                "Downloading Hindi audio"
            )

        if "hindi_video" not in completed_stages:
            logger.info("Hindi video not completed. Generating video.")

            hindi_video_path = self.retry_operation(
                lambda: self.generate_video(
                    hindi_audio_path,
                    image_path,
                    "Hindi"
                ),
                "Hindi video generation"
            )

            self.retry_operation(
                lambda: upload_artifact(
                    None,
                    hindi_video_path,
                    f"runs/{self.session_id}/hindi/video.mp4"
                ),
                "Uploading Hindi video"
            )

            state["stage"] = "hindi_video"
            completed_stages.append("hindi_video")
            write_state(state)

        else:
            logger.info("Hindi video already completed. Downloading video.")

            hindi_video_path = f"artifacts/videos/{self.session_id}_hindi.mp4"

            self.retry_operation(
                lambda: download_artifact(
                    f"runs/{self.session_id}/hindi/video.mp4",
                    hindi_video_path
                ),
                "Downloading Hindi video"
            )

        if "hindi_upload" not in completed_stages:
            logger.info("Hindi video not uploaded. Uploading.")

            self.retry_operation(
                lambda: self.upload_video(
                    hindi_script,
                    hindi_video_path,
                    "Hindi"
                ),
                "Hindi video upload"
            )

            state["stage"] = "hindi_upload"
            completed_stages.append("hindi_upload")
            write_state(state)

        else:
            logger.info("Hindi video already uploaded.")

        state["stage"] = "complete"
        state["session_id"] = None

        write_state(state)

        logger.info(
            "Pipeline completed successfully for topic: %s",
            topic
        )