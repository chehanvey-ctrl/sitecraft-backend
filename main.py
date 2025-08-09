# main.py
import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from github import Github
import openai

# -----------------------------
# Config & Clients
# -----------------------------
app = FastAPI(title="SiteCraft Backend")

# Frontend(s) that are allowed to call this API
ALLOWED_ORIGINS = [
    "https://sitecraft-pages.vercel.app",
    "https://t-pages.vercel.app",
]

# Allow any *.vercel.app subdomain as well (handy for previews)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Env
openai.api_key = os.getenv("OPENAI_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO_FULL_NAME = os.getenv("GITHUB_REPO", "chehanvey-ctrl/sitecraft-pages")
LIVE_SITE_URL = os.getenv("LIVE_SITE_URL", "https://sitecraft-pages.vercel.app")
VERCEL_DEPLOY_HOOK_URL = os.getenv("VERCEL_DEPLOY_HOOK_URL", "")
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")  # not required if using the hook

# -----------------------------
# Models
# -----------------------------
class PromptRequest(BaseModel):
    prompt: str

# -----------------------------
# Utility helpers
# -----------------------------
def generate_image_url(prompt: str) -> str:
    """Generate a background image; fall back to Unsplash if it fails."""
    default_img = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"
    try:
        resp = openai.images.generate(
            model="dall-e-3",
            prompt=f"{prompt}, professional background image, no text, visually clean and accurate to theme.",
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url",
        )
        return resp.data[0].url
    except Exception as e:
        print(f"[Image Error] {e}")
        return default_img

def generate_html(prompt: str, image_url: str) -> str:
    """Ask the model to return full HTML with embedded CSS (no markdown fences)."""
    try:
        resp = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.7,
            max_tokens=1800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're a top web designer. Return ONLY valid HTML (with embedded <style>) for a fully "
                        "responsive one-page site. No markdown fences. Include:\n"
                        "- Full-width hero with the provided image (no overlay text on the image itself)\n"
                        "- An eye-catching creative title inside the hero\n"
                        "- ~5 themed sections; soft gradients/borders; clean spacing and typography\n"
                        "- Simple footer\n"
                        "All copy must relate directly to the user's prompt. No lorem ipsum."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Prompt: {prompt}\nHero image: {image_url}",
                },
            ],
        )
        html = resp.choices[0].message.content.strip()

        # Remove stray markdown fences if the model added them
        if html.startswith("```"):
            html = html.strip("` \n")
            if html.lower().startswith("html"):
                html = html[4:].lstrip()

        return html
    except Exception as e:
        print(f"[HTML Error] {e}")
        return f"<h1>SiteCraft Error</h1><p>{e}</p>"

def commit_to_github(html_code: str, path: str = "index.html") -> None:
    """Create or update index.html on main branch."""
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is not set")
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_FULL_NAME)
        message = "SiteCraft auto-update"
        try:
            contents = repo.get_contents(path, ref="main")
            repo.update_file(path, message, html_code, contents.sha, branch="main")
        except Exception:
            repo.create_file(path, message, html_code, branch="main")
    except Exception as e:
        raise RuntimeError(f"GitHub commit failed: {e}")

def trigger_vercel_deploy() -> None:
    """
    Trigger a Vercel deployment.
    Prefer the Deploy Hook URL (no auth required).
    """
    if VERCEL_DEPLOY_HOOK_URL:
        try:
            r = requests.post(VERCEL_DEPLOY_HOOK_URL, timeout=15)
            r.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Vercel deploy hook failed: {e}")
    else:
        # Optional: add Vercel API fallback here if you want to use VERCEL_TOKEN
        print("[Vercel] No deploy hook configured; skipping auto-deploy.")

# -----------------------------
# Health & Preflight (OPTIONS)
# -----------------------------
@app.get("/health")
async def health():
    return {"ok": True, "service": "sitecraft-backend"}

# Explicit OPTIONS handlers to satisfy browsers in case middleware misses it
@app.options("/generate-pure")
async def options_generate(_: Request):
    return JSONResponse(content={"ok": True}, status_code=200)

@app.options("/publish")
async def options_publish(_: Request):
    return JSONResponse(content={"ok": True}, status_code=200)

# -----------------------------
# Endpoints
# -----------------------------
@app.post("/generate-pure")
async def generate_pure_site(req: PromptRequest):
    """
    Returns HTML only (used for quick preview/download).
    """
    image_url = generate_image_url(req.prompt)
    html_code = generate_html(req.prompt, image_url)
    return {"html": html_code}

@app.post("/publish")
async def publish_site(req: PromptRequest):
    """
    1) Generate image + HTML
    2) Commit to GitHub repo (index.html on main)
    3) Trigger Vercel deploy (via deploy hook)
    4) Return HTML and the live site URL for the frontend CTA
    """
    # 1 & 2: generate
    image_url = generate_image_url(req.prompt)
    html_code = generate_html(req.prompt, image_url)

    # If model somehow returned nothing, guard it
    if not html_code or "<html" not in html_code.lower():
        return JSONResponse(
            status_code=500,
            content={"error": "HTML generation failed", "html": html_code or ""},
        )

    # 3: push to GitHub
    try:
        commit_to_github(html_code, path="index.html")
    except Exception as e:
        # Return HTML so the user can still preview, and show the error
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "html": html_code},
        )

    # 4: trigger Vercel deploy (non-blocking from user POV)
    try:
        trigger_vercel_deploy()
    except Exception as e:
        # Not fatal for the user flow; site might still serve previous content
        print(e)

    return {"html": html_code, "live_url": LIVE_SITE_URL}

# --------------- Run ---------------
# Render/uvicorn will run via Procfile/Start Command; nothing to do here.
