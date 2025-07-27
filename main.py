from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from openai import OpenAI

class PromptRequest(BaseModel):
    prompt: str

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/generate")
async def generate(request: PromptRequest):
    prompt = request.prompt

    # Generate image using DALL·E
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024"
    )
    image_url = image_response.data[0].url

    # Generate HTML using GPT-4
    chat_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Generate a clean, modern, beautiful HTML5 landing page for the following request. Include the provided image as a hero/banner visual."},
            {"role": "user", "content": f"{prompt}\n\nImage URL: {image_url}"}
        ]
    )

    html_code = chat_response.choices[0].message.content
    return JSONResponse(content={"html": html_code})
