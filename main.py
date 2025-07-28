from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SiteRequest(BaseModel):
    prompt: str

@app.post("/generate-site")
async def generate_site(request: SiteRequest):
    user_prompt = request.prompt

    # Prompt for text (HTML/CSS)
    chat_prompt = [
        {"role": "system", "content": "You are a helpful website generator that only outputs HTML and Tailwind CSS."},
        {"role": "user", "content": f"{user_prompt}. Only return HTML and Tailwind CSS. Do not include <script> tags."}
    ]

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=chat_prompt,
        temperature=0.7,
        max_tokens=2000
    )

    website_code = completion.choices[0].message.content

    # Prompt for AI image
    image_prompt = "Create an AI image of a humanoid robot prototype with neon accents in a futuristic lab setting"
    
    image_response = client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )

    # ✅ FIX: Access response using object-style (not dictionary-style)
    image_url = image_response.data[0].url

    # Inject image block below the <main> but above the first section
    enhanced_code = website_code.replace(
        "<main>",
        f"""<main>
    <section class="w-full flex justify-center items-center bg-black py-10">
      <img src="{image_url}" alt="AI generated visual" class="rounded-xl shadow-lg max-w-[80%]" />
    </section>
"""
    )

    return {"html": enhanced_code}
