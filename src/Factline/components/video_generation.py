import subprocess
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
                print(f"Error: {file} not found in current directory")
                return False

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
            print(f"Error creating video: {e}")
            return None


    # def create_video(self,session_id):
    #     # File paths
    #     output_video = f"artifacts/videos/{session_id}.mp4"
    #     # Video settings
    #     width = 768
    #     height = 1344
        
    #     # Text settings
    #     text_content = "This is an AI Generated Image and is NOT real"  # Change this to your desired text
    #     font_size = 24
        
    #     # Check if required files exist
    #     audio = self.config.audio
    #     background_image = self.config.background_image
    #     logo_image = self.config.logo_image
    #     required_files = [audio, background_image, logo_image]
    #     for file in required_files:
    #         if not os.path.exists(file):
    #             print(f"Error: {file} not found in current directory")
    #             return False
        
    #     # FFmpeg command with showwaves filter for full-width waveform
    #     ffmpeg_cmd = [
    #         "ffmpeg",
    #         "-y",
    #         "-i", audio,
    #         "-loop","1"
    #         "-i", background_image,
    #         "-i", logo_image,
    #         "-filter_complex",
    #         f"""
    #         [1:v]scale={width}:{height}[bg];
    #         [bg]drawtext=text='{text_content}':
    #             fontcolor=white:
    #             fontsize={font_size}:
    #             x=20:y=20[bg_with_text];
    #         [2:v]scale=60:60[logo_scaled];
    #         [bg_with_text][logo_scaled]overlay={width-80}:{height-80}[final]
    #         """,
    #         "-map", "[final]",
    #         "-map", "0:a",
    #         "-c:v", "libx264",
    #         "-c:a", "aac",
    #         "-pix_fmt", "yuv420p",
    #         "-r", "30",
    #         "-shortest",
    #         output_video
    #     ]
        
        
    #     try:
    #         result = subprocess.run(ffmpeg_cmd, 
    #                             capture_output=True, 
    #                             text=True, 
    #                             check=True)
    #     except subprocess.CalledProcessError as e:
    #         return None
    #     except FileNotFoundError:
    #         return None
    #     return output_video