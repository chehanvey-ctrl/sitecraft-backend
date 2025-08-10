from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from github import Github

# ----------------------------
# FastAPI setup
# ----------------------------
app = FastAPI()

# CORS: include all current frontends you use
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sitecraft-frontend.onrender.com",  # old Render frontend
        "https://t-pages.vercel.app",               # Vercel project frontend (if used)
        "https://sitecraft.eu",                     # custom domain frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Environment / SDK setup
# ----------------------------
openai.api_key = os.getenv("OPENAI_API_KEY")
github_token = os.getenv("GITHUB_TOKEN")

# Request model
class PromptRequest(BaseModel):
    prompt: str

# ----------------------------
# Endpoint: Generate full HTML site (preview only; no publish)
# ----------------------------
@app.post("/generate-pure")
async def generate_pure_site(request: PromptRequest):
    prompt = request.prompt
    image_url = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"  # fallback

    # 1) Generate hero image (no text)
    try:
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"{prompt}, professional background image, no text, visually clean and accurate to theme.",
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url",
        )
        image_url = image_response.data[0].url
    except Exception as e:
        print(f"[Image Error] {e}")

    # 2) Generate full HTML
    try:
        html_response = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a top web designer. Build a fully responsive, modern one-page website using HTML and embedded CSS. Include:\n"
                        "- Full-width hero section with the image provided (no overlay text)\n"
                        "- An eye-catching creative title inside the hero\n"
                        "- 5 themed content sections with soft gradients or colored backgrounds and visual borders\n"
                        "- Clean typography, spacing, and visual clarity\n"
                        "- A simple footer\n"
                        "All content must relate directly to the user prompt. Do NOT use 'lorem ipsum'."
                    )
                },
                {
                    "role": "user",
                    "content": f"Prompt: {prompt}\nHero image: {image_url}"
                }
            ],
        )
        html_code = html_response.choices[0].message.content.strip()
    except Exception as e:
        html_code = f"<h1>SiteCraft Error</h1><p>{e}</p>"

    return {"html": html_code}

# ----------------------------
# Endpoint: Publish freshly generated HTML (regenerates & publishes)
# ----------------------------
@app.post("/publish")
async def publish_site(request: PromptRequest):
    prompt = request.prompt
    image_url = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"  # fallback

    # 1) Generate hero image (no text)
    try:
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"{prompt}, professional background image, no text, visually clean and accurate to theme.",
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url",
        )
        image_url = image_response.data[0].url
    except Exception as e:
        print(f"[Image Error] {e}")

    # 2) Generate full HTML from GPT
    try:
        html_response = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a top web designer. Build a fully responsive, modern one-page website using HTML and embedded CSS. Include:\n"
                        "- Full-width hero section with the image provided (no overlay text)\n"
                        "- An eye-catching creative title inside the hero\n"
                        "- 5 themed content sections with soft gradients or colored backgrounds and visual borders\n"
                        "- Clean typography, spacing, and visual clarity\n"
                        "- A simple footer\n"
                        "All content must relate directly to the user prompt. Do NOT use 'lorem ipsum'."
                    )
                },
                {
                    "role": "user",
                    "content": f"Prompt: {prompt}\nHero image: {image_url}"
                }
            ],
        )
        html_code = html_response.choices[0].message.content.strip()
    except Exception as e:
        return {"html": f"<h1>HTML Error</h1><p>{e}</p>"}

    # 3) Push to GitHub (sitecraft-pages)
    try:
        g = Github(github_token)
        repo = g.get_repo("chehanvey-ctrl/sitecraft-pages")
        file_path = "index.html"
        commit_message = f"Update site: {prompt[:50]}"

        try:
            contents = repo.get_contents(file_path)
            repo.update_file(file_path, commit_message, html_code, contents.sha, branch="main")
        except Exception:
            repo.create_file(file_path, commit_message, html_code, branch="main")
    except Exception as e:
        return {"html": f"<h1>GitHub Error</h1><p>{e}</p>"}

    return {
        "html": html_code,
        "live_url": "https://sitecraft-pages.vercel.app",
    }

# ----------------------------
# NEW Endpoint: Publish EXACT HTML from the frontend (preserves user edits)
# ----------------------------
@app.post("/publish-html")
async def publish_html_direct(html: str = Body(..., embed=True)):
    """
    Accept final HTML from the frontend (after user edits),
    push it to GitHub (sitecraft-pages), and return the live Vercel URL.
    """
    # 1) Validate payload
    if not html or "<html" not in html.lower():
        return {"error": "Invalid HTML payload."}

    # 2) Push to GitHub
    try:
        g = Github(github_token)
        repo = g.get_repo("chehanvey-ctrl/sitecraft-pages")  # keep your working repo
        file_path = "index.html"
        commit_message = "Publish edited site from SiteCraft UI"

        try:
            contents = repo.get_contents(file_path)
            repo.update_file(file_path, commit_message, html, contents.sha, branch="main")
        except Exception:
            repo.create_file(file_path, commit_message, html, branch="main")
    except Exception as e:
        return {"error": f"GitHub Error: {e}"}

    return {
        "live_url": "https://sitecraft-pages.vercel.app",
    }
