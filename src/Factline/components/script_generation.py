from Factline.config.configuration import SystemPrompt,CHAT_MODEL
from Factline.config.models import NewsScript
from box import ConfigBox

class ScriptGen:
    def __init__(self,config):
        self.config = config

    def news_script(self):
        print(self.config.transcript)
        system_prompt = SystemPrompt.script_prompt(self.config.topic, self.config.language, self.config.transcript)
        script = CHAT_MODEL.with_structured_output(NewsScript).invoke([("system",system_prompt),("user","")])
        return ConfigBox(script.model_dump())
    

