from Factline import logger
import os
from dotenv import load_dotenv
from moviepy import ImageClip, AudioFileClip, TextClip, CompositeVideoClip

load_dotenv()

class VideoGen:
    def __init__(self,config):
        self.config = config
    def create_video(self, session_id):
        output_video = f"artifacts/videos/{session_id}.mp4"
        width = 768
        height = 1344
        text_content = "This is an AI Generated Image and is NOT real"
        font_size = 24
        audio = self.config.audio
        background_image = self.config.background_image
        logo_image = self.config.logo_image

        required_files = [audio, background_image, logo_image]

        for file in required_files:
            if not os.path.exists(file):
                logger.exception("%s file not present, video cannot be generated")
                raise

        try:
            audio_clip = AudioFileClip(audio)
            background = (
                ImageClip(background_image)
                .resized((width, height))
                .with_duration(audio_clip.duration)
            )

            text_clip = (
                TextClip(
                    text=text_content,
                    font_size=font_size,
                    color="white"
                )
                .with_position((20, 20))
                .with_duration(audio_clip.duration)
            )

            logo = (
                ImageClip(logo_image)
                .resized((60, 60))
                .with_position((width - 80, height - 80))
                .with_duration(audio_clip.duration)
            )

            final_video = CompositeVideoClip(
                [
                    background,
                    text_clip,
                    logo
                ],
                size=(width, height)
            )

            final_video = final_video.with_audio(audio_clip)

            final_video.write_videofile(
                output_video,
                fps=30,
                codec="libx264",
                audio_codec="aac"
            )

            audio_clip.close()
            final_video.close()

            return output_video

        except Exception as e:
            logger.exception("Failed to create due to the following error : %s",e)
            raise
