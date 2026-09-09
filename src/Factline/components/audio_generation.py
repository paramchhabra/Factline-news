from openai import OpenAI, OpenAIError
from dotenv import load_dotenv
from Factline import logger

load_dotenv()

class AudioGen:
    def __init__(self,config):
        self.config = config

    def generate_speech(self):
        try:
            client = OpenAI()
            response =  client.audio.speech.create(
                model=self.config.model,
                voice=self.config.voice,
                input=self.config.input,
                instructions=self.config.instructions)
            logger.info(f"OpenAI audio created")
            return response
        except OpenAIError as e:
            logger.error(f"OpenAI TTS API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in generate_speech: {e}")