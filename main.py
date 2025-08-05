from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from jinja2 import Template
import uuid
import requests

# Initialize FastAPI app
app = FastAPI()

# Allow only your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-pages.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup OpenAI with secure API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Request body model
class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate-pure")
async def generate_pure_site(request: PromptRequest):
    prompt = request.prompt

    # 1. Generate AI image with DALL·E 3
    image_response = openai.images.generate(
        model="dall-e-3",
        prompt=prompt,
        n=1,
        size="1024x1024",
        quality="standard",
        response_format="url"
    )
    image_url = image_response.data[0].url

    # 2. Generate full HTML site using GPT-4o
    gpt_prompt = f"""Generate a full HTML5 website with modern styling and CSS.
The theme is: "{prompt}". The site should include the following:
- An AI-generated image at the top from this URL: {image_url}
- A bold hero section
- A catchy tagline below the hero
- At least 3 content sections
- Modern, responsive design
Return only the raw HTML code, no explanation.
"""

    chat_response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": gpt_prompt}]
    )

    html_code = chat_response.choices[0].message.content

    # 3. Save to local file for upload
    file_name = f"{str(uuid.uuid4())[:8]}.html"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html_code)

    # 4. Create Vercel project
    vercel_token = os.getenv("VERCEL_TOKEN")
    headers = {
        "Authorization": f"Bearer {vercel_token}",
        "Content-Type": "application/json"
    }

    project_name = f"sitecraft-{str(uuid.uuid4())[:8]}"

    project_payload = {
        "name": project_name,
        "framework": "vite",
        "buildCommand": "",
        "outputDirectory": "",
        "rootDirectory": "",
    }

    requests.post("https://api.vercel.com/v9/projects", headers=headers, json=project_payload)

    # 5. Upload file to Vercel
    with open(file_name, "rb") as f:
        files = {
            "file": (file_name, f, "text/html"),
        }
        upload_response = requests.post(
            f"https://api.vercel.com/v13/files",
            headers=headers,
            files=files
        )

    file_data = upload_response.json()
    file_hash = file_data.get("digest")

    # 6. Deploy the uploaded file
    deployment_payload = {
        "name": project_name,
        "files": [
            {
                "file": "index.html",
                "data": file_hash
            }
        ],
        "projectSettings": {
            "framework": "other"
        },
        "routes": [
            {
                "src": "/(.*)",
                "dest": "index.html"
            }
        ]
    }

    deploy_response = requests.post(
        "https://api.vercel.com/v13/deployments",
        headers=headers,
        json=deployment_payload
    )

    live_url = f"https://{project_name}.vercel.app"

    return {
        "html": html_code,
        "site_url": live_url
    }
