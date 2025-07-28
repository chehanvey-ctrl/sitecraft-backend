import os
import openai
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class PromptRequest(BaseModel):
    prompt: str

# HTML template wrapper
def build_html_with_image(image_url: str, site_text: str) -> str:
    return f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .hero {{
                text-align: center;
                padding: 30px;
                background-color: #ffffff;
            }}
            .hero img {{
                width: 100%;
                max-height: 300px;
                object-fit: cover;
                border-radius: 8px;
            }}
            .content {{
                padding: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="hero">
            <img src="{image_url}" alt="Generated Image">
        </div>
        <div class="content">
            {site_text}
        </div>
    </body>
    </html>
    """

# Generate route
@app.post("/generate")
async def generate_website(data: PromptRequest):
    try:
        # TEXT: Generate clean HTML text content
        text_response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior web designer who writes clean, semantic HTML for simple personal or business websites. Do NOT include images or image tags. Focus on layout and good copywriting with proper structure."
                },
                {
                    "role": "user",
                    "content": data.prompt
                }
            ]
        )

        site_text = text_response.choices[0].message.content

        # IMAGE: Generate one DALL·E image based on prompt
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=data.prompt,
            n=1,
            size="1024x1024"
        )
        image_url = image_response.data[0].url

        # Combine HTML layout and image
        final_html = build_html_with_image(image_url, site_text)
        return {"html": final_html}

    except Exception as e:
        return {"error": str(e)}
