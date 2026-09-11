import base64
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class ImageGen:
    def __init__(self, config):
        self.config = config

    def create_bg_img(self):
        self.config.api_key = os.getenv("STABILITY_AI_API")
        if self.config.api_key is None:
            raise Exception("Missing Stability API key.")

        response = requests.post(
            f"{self.config.api_host}/v1/generation/{self.config.engine_id}/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            },
            json={
                "text_prompts": [
                    {
                        "text": self.config.prompt
                    }
                ],
                "cfg_scale": 7,
                "height": 1344,
                "width": 768,
                "samples": 1,
                "steps": 30,
            },
        )

        if response.status_code != 200:
            raise Exception("Non-200 response: " + str(response.text))

        data = response.json()

        image = base64.b64decode(data["artifacts"][0]["base64"])
        
        return image