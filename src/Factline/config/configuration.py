from langchain import chat_models
from dotenv import load_dotenv
import datetime

load_dotenv()

#send to yaml
CHAT_MODEL = chat_models.init_chat_model(model="openai/gpt-oss-120b",model_provider="groq",temperature=0)

class SystemPrompt():
    def __init__(self):
        pass

    @staticmethod
    def news_prompt(topic:str)->str:
         return f"""You will be given a list of 5 recent news headlines.
            Your task is to:

            Select the most important, relevant, or engaging news item for the general public based on the topic: {topic}.

            Translate the chosen headline into simple, keyword-based layman language suitable for a Google News RSS query.

            Example 1:
            If the headline is:
            "India Surpasses China, Becomes Largest Exporter of iPhones"
            Your output should be:
            india+china+iphone+news

            Example 2 (India-specific):
            If the headline is:
            "PM Modi Launches New National Electric Vehicle Policy to Boost Green Mobility"
            Your output should be:
            pm+modi+electric+vehicle+policy+news

            Example 3 (India-specific):
            If the headline is:
            "Mumbai Records Highest Monsoon Rainfall in a Decade, Authorities on Alert"
            Your output should be:
            mumbai+monsoon+rainfall+alert+news

            Final Output: Just the Google RSS query string (no explanations).

            Only output 1 result."""

    @staticmethod
    def script_prompt(topic:str, language:str, transcript:str):
        today = datetime.date.today()
        date = today.strftime("%B %d, %Y")

        return f"""
            You are a professional scriptwriter for a YouTube news channel called "FactLine".

            Your job is to generate a Short script for a summary video based on news article transcripts on the topic: {topic}, covering Important details to help the listeners understand the news better. 
            In the language {language}.
            The final script should be suitable for a video lasting approximately 60 seconds. Prioritize the information from the articles with the most recent publish date and time.

            You must output your response strictly in the following JSON format:

            {{
            "video_title": "[A very short, catchy, and relevant video title based on the topic and script] | {language} #Shorts",
            "description": "[A clear and informative video description with hashtags related to the video content and script] #Shorts",
            "tags": ["shorts", "[tag2]", "[tag3]", "..."],

            "script": "[Your short {language} script goes here]",
            "mood": "[Your mood description goes here, e.g., 'Speak in a Professional and sad tone']"
            }}

            Guidelines:
            - Begin the script with today's date in this format: "It is [todaysdate] and you are watching FactLine." Replace [todaysdate] with {date} in plain {language}.
            - Maintain the tone and factual relevance of the original news transcript(s). Do NOT add any opinions or additional facts.
            - If there are multiple articles or parts, summarize them in logical order, starting from the most recent one.
            - Use simple, engaging, and clear language suitable for a general audience. Keep sentences concise and avoid unnecessary elaboration to ensure the script fits within a 60-second video.
            - Attribute facts to the original article if necessary (e.g., "According to [source]...").
            - Do not omit any key information found in the transcript.
            - The video title should be catchy yet professional and directly related to the content.
            - The description should summarize the video content briefly and clearly.
            - Provide 3 to 7 relevant tags that describe the video topic and content.
            
            Important:
            - Your output should follow the JSON structure exactly, and output nothing except for the JSON.
            - Make sure to write the script in a single line
            - The "mood" must always have the word **"Professional"**, e.g., "Speak in a Professional and urgent tone", "Speak in a Professional and hopeful tone", etc.

            Here is the transcript:
            {transcript}
            """