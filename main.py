from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/generate-site")
async def generate_site(request: Request):
    data = await request.json()
    prompt = data.get("prompt")

    try:
        # AI Image generation using DALL·E
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )

        # Extract image URL
        image_url = image_response.data[0].url

        # HTML Generation prompt
        html_prompt = (
            "Generate a complete HTML5 one-page personal website with modern design. "
            "Use Tailwind CSS from CDN. The prompt for the site is: " + prompt + ". "
            f"Add an AI-generated image just below the hero section using this tag: <img src='{image_url}' alt='AI generated image' class='w-full rounded-lg my-6' />. "
            "Make the layout sleek, visually appealing, and mobile responsive. "
            "Do not include <html>, <head>, or <body> tags—just the main content for a single-page app."
        )

        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a modern HTML and Tailwind CSS expert."},
                {"role": "user", "content": html_prompt}
            ]
        )

        site_code = completion.choices[0].message.content
        return {"code": site_code, "image_url": image_url}

    except Exception as e:
        return {"error": str(e)}
