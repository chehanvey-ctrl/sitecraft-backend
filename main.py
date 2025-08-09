# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import re
import json
import requests
import openai
from github import Github

# ─────────────────────────────────────────────────────────
# Config / Env
# ─────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
VERCEL_DEPLOY_HOOK = os.getenv("VERCEL_DEPLOY_HOOK")  # <-- you added this
LIVE_SITE_URL = "https://sitecraft-pages.vercel.app"

openai.api_key = OPENAI_API_KEY

# ─────────────────────────────────────────────────────────
# FastAPI
# ─────────────────────────────────────────────────────────
app = FastAPI()

# Allow your Vercel frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://t-pages.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class PromptRequest(BaseModel):
    prompt: str

# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def clean_html_content(text: str) -> str:
    """Remove ``` fences and try to extract a full HTML document if present."""
    if not text:
        return text
    # Strip triple backticks blocks like ```html ... ```
    text = re.sub(r"^```(?:html|HTML)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    # If the model returned extra prose, try to extract the <html>...</html> block
    m = re.search(r"<html[\s\S]*?</html>", text, flags=re.IGNORECASE)
    return m.group(0).strip() if m else text.strip()

def trigger_vercel_deploy():
    """Fire-and-forget Vercel deploy hook. Returns (ok, status, body)."""
    if not VERCEL_DEPLOY_HOOK:
        return False, 0, "Missing VERCEL_DEPLOY_HOOK"
    try:
        resp = requests.post(VERCEL_DEPLOY_HOOK, timeout=10)
        body = ""
        try:
            body = resp.text
        except Exception:
            body = "<no body>"
        return resp.ok, resp.status_code, body
    except Exception as e:
        return False, 0, str(e)

def generate_image_url(prompt: str) -> str:
    """Try to get a hero image URL; fall back to Unsplash if it fails."""
    fallback = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"
    try:
        img = openai.images.generate(
            model="dall-e-3",
            prompt=f"{prompt}, professional background image, no text, visually clean and accurate to theme.",
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url",
        )
        return img.data[0].url or fallback
    except Exception as e:
        print(f"[Image Error] {e}")
        return fallback

def generate_html(prompt: str, image_url: str) -> str:
    """Ask the model for a single-file HTML page and clean the output."""
    try:
        resp = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a top web designer. Build a fully responsive, modern one-page website using "
                        "HTML and embedded CSS only (no external CSS/JS). Include:\n"
                        "- Full-width hero section that uses the provided hero image (no overlay text ON the image itself)\n"
                        "- An eye-catching creative title inside the hero area (as page content)\n"
                        "- 5 themed content sections with soft gradients or colored backgrounds and subtle borders\n"
                        "- Clean typography, spacing, and visual clarity\n"
                        "- A simple footer\n"
                        "All content must directly relate to the user's prompt. Do NOT use lorem ipsum.\n"
                        "Return ONLY a valid HTML document (starting with <html> and ending with </html>)."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Prompt: {prompt}\nHero image: {image_url}",
                },
            ],
        )
        raw = resp.choices[0].message.content or ""
        return clean_html_content(raw)
    except Exception as e:
        raise RuntimeError(f"OpenAI HTML generation failed: {e}")

def push_to_github(html_code: str, prompt: str):
    """Create/update index.html in the sitecraft-pages repo."""
    if not GITHUB_TOKEN:
        raise RuntimeError("Missing GITHUB_TOKEN env var.")
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo("chehanvey-ctrl/sitecraft-pages")
        file_path = "index.html"
        commit_message = f"Update site: {prompt[:50]}"

        try:
            contents = repo.get_contents(file_path, ref="main")
            repo.update_file(file_path, commit_message, html_code, contents.sha, branch="main")
        except Exception:
            repo.create_file(file_path, commit_message, html_code, branch="main")
    except Exception as e:
        raise RuntimeError(f"GitHub push failed: {e}")

# ─────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"ok": True, "service": "sitecraft-backend"}

@app.post("/generate-pure")
async def generate_pure_site(request: PromptRequest):
    prompt = (request.prompt or "").strip()
    if not prompt:
        return {"html": "<h1>SiteCraft Error</h1><p>Prompt is empty.</p>"}

    image_url = generate_image_url(prompt)

    try:
        html_code = generate_html(prompt, image_url)
        if not html_code or "<html" not in html_code.lower():
            return {"html": "<h1>SiteCraft Error</h1><p>Model did not return valid HTML.</p>"}
    except Exception as e:
        return {"html": f"<h1>SiteCraft Error</h1><p>{e}</p>"}

    return {"html": html_code}

@app.post("/publish")
async def publish_site(request: PromptRequest):
    prompt = (request.prompt or "").strip()
    if not prompt:
        return {"html": "<h1>SiteCraft Error</h1><p>Prompt is empty.</p>"}

    # 1) image
    image_url = generate_image_url(prompt)

    # 2) html
    try:
        html_code = generate_html(prompt, image_url)
        if not html_code or "<html" not in html_code.lower():
            return {"html": "<h1>HTML Error</h1><p>Model did not return valid HTML.</p>"}
    except Exception as e:
        return {"html": f"<h1>HTML Error</h1><p>{e}</p>"}

    # 3) push to GitHub
    try:
        push_to_github(html_code, prompt)
    except Exception as e:
        return {"html": f"<h1>GitHub Error</h1><p>{e}</p>"}

    # 4) trigger Vercel deployment (fire & forget)
    ok, status, body = trigger_vercel_deploy()
    if not ok:
        # We still return live_url so the button works, but include info so you can debug.
        print(f"[Vercel Hook Warning] status={status} body={body}")

    # 5) tell the frontend where the live site will be
    return {
        "html": html_code,
        "live_url": LIVE_SITE_URL,   # frontend uses this for the button + success page
        "vercel_hook_ok": ok,
        "vercel_hook_status": status,
    }
