from Factline.components.news_fetch import NewsData
from Factline.components.script_generation import ScriptGen
from Factline.components.audio_generation import AudioGen
from Factline.components.image_generation import ImageGen
from Factline.components.video_generation import VideoGen
from Factline.utils.helper import read_config
from box import ConfigBox
import datetime
import base64

session_id = datetime.datetime.now().strftime("%y%m%d%H%M%S")
config = read_config()
print(session_id)

# # self.config.topic, self.config.language, self.config.transcript
news_class = NewsData("","sports")
data = news_class.get_news_data()

script_data = ConfigBox({"topic":"sports","language":"English","transcript":data})
script_class = ScriptGen(script_data)
script = script_class.news_script()

audio_data = config.audio_model
audio_data.input = script.script
audio_class = AudioGen(audio_data)
with open(f"artifacts/audio/{session_id}.mp3","wb") as audio_file:
    audio_file.write(audio_class.generate_speech().read())

image_data = config.image_model
image_data.prompt = script.video_title
image_class = ImageGen(image_data)
with open(f"artifacts/images/{session_id}.png","wb") as image_file:
    image_file.write(image_class.create_bg_img())

video_data = config.video_model
video_data.audio = f"artifacts/audio/{session_id}.mp3"
video_data.background_image = f"artifacts/images/{session_id}.png"
video_data.logo_image = f"artifacts/images/logo.png"
video_class = VideoGen(video_data)
video = video_class.create_video(session_id)




