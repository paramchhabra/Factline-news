from pydantic import BaseModel,field_validator,Field,ConfigDict

class NewsQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query:str

    @field_validator("query")
    @classmethod
    def validate_news_query(cls,query:str):
        parts = query.split("+")
        if len(parts)<2:
            raise ValueError("LLM Generated output without +")
        return query

class NewsScript(BaseModel):
        video_title:str = Field(description="A very short, catchy, and relevant video title based on the topic and script | {language\} #Shorts")
        description:str = Field(description="A clear and informative video description with hashtags related to the video content and script | #Shorts")
        tags:list = Field(description="[shorts, [tag2], [tag3],...]")
        script:str = Field(description="Your short script goes here")
        mood:str = Field(description="Your mood description goes here, e.g., 'Speak in a Professional and sad tone'")
        model_config = ConfigDict(extra="forbid")