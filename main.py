# main.py
import os
import base64
import json
from datetime import datetime
from typing import Optional, Dict, Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ===== OpenAI (official SDK) =====
try:
    from openai import OpenAI
except Exception:  # fallback for older installs named "openai"
    import openai  # type: ignore
    class OpenAI:  # minimal adapter
        def __init__(self, api_key: str | None = None):
            openai.api_key = api_key or os.getenv("OPENAI_API_KEY")
        @property
        def chat(self):
            return openai.ChatCompletion  # type: ignore
        @property
        def images(self):
            return openai.Image  # type: ignore

# -------------------------------------------------
# Environment
# -------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
PAGES_REPO = os.getenv("PAGES_REPO", "")  # e.g. "chehanvey-ctrl/sitecraft-pages"
PAGES_BRANCH = os.getenv("PAGES_BRANCH", "main")
PAGES_FILEPATH = os.getenv("PAGES_FILEPATH", "index.html")

LIVE_BASE_URL = os.getenv("LIVE_BASE_URL", "https://sitecraft-pages.vercel.app")
VERCEL_DEPLOY_HOOK_URL = os.getenv("VERCEL_DEPLOY_HOOK_URL", "")  # optional

USE_IMAGE = os.getenv("USE_IMAGE", "true").lower() in ("1", "true", "yes")

# -------------------------------------------------
# FastAPI + CORS
# -------------------------------------------------
app = FastAPI(title="SiteCraft Backend")

allowed_origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.vercel.app",
    LIVE_BASE_URL,
    os.getenv("FRONTEND_ORIGIN", ""),
]
# keep it simple—allow credentials false
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in allowed_origins if o],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Models
# -------------------------------------------------
class GenReq(BaseModel):
    prompt: str

class PubReq(BaseModel):
    prompt: str

# -------------------------------------------------
# OpenAI client
# -------------------------------------------------
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required.")

client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------------------------------
# Prompts (updated: grammar perfect + no text in images)
# -------------------------------------------------
WEB_COPY_SYSTEM_PROMPT = """You are a senior web copywriter and frontend designer.
Generate a single COMPLETE HTML document (<!DOCTYPE html> through </html>) with light inline CSS only.
Requirements:
- Use clear, concise English with PERFECT grammar, spelling, and punctuation.
- No placeholder typos or stretched words. Avoid shouting; use Title Case where appropriate.
- All headings and taglines must be correctly spelled (e.g., “Serving Happiness in Every Bite”).
- Keep content friendly and professional. No slang unless requested.
- Mobile-first, semantic HTML (header, main, section, footer), accessible contrast and alt text.
- If an image URL is provided in the USER message, use it; DO NOT embed base64 images.
- Do NOT rely on any external CSS/JS frameworks or CDNs.
Return ONLY the HTML document."""

def build_image_prompt(user_prompt: str) -> str:
    # Add the crucial “no text in image” constraint
    return (
        f"{user_prompt}. Create an aesthetically pleasing website hero/background image. "
        "Absolutely do NOT include any text, words, lettering, logos, watermarks, signage, or typography."
    )

# -------------------------------------------------
# Utilities
# -------------------------------------------------
def generate_image_b64(user_prompt: str) -> Optional[str]:
    """
    Generates an image (base64). We keep this to avoid breaking the current
    frontend that already shows hero images. If you later host images, you can
    switch to returning a URL instead.
    """
    try:
        # New SDK style
        if hasattr(client, "images") and hasattr(client.images, "generate"):
            resp = client.images.generate(
                model="gpt-image-1",  # or "dall-e-3" if you use that
                prompt=build_image_prompt(user_prompt),
                size="1024x1024",
            )
            # OpenAI returns base64 in data[0].b64_json
            b64 = resp.data[0].b64_json  # type: ignore[attr-defined]
            return b64
        # Old SDK fallback (not expected nowadays)
        return None
    except Exception as e:
        # Don't fail HTML if image fails—just return None
        print(f"[image] generation failed: {e}")
        return None

def generate_html_copy(user_prompt: str, image_b64: Optional[str]) -> str:
    """
    Generates complete HTML. If image_b64 is present, we’ll embed it;
    otherwise we’ll produce a clean layout without the hero image.
    """
    user_instructions = user_prompt.strip()
    # We pass a hint about image presence to the model (but we still embed b64 ourselves if available)
    if image_b64:
        user_instructions += "\n\n[Note for you: A hero image is available and will be embedded by the server.]"

    try:
        # New SDK style
        if hasattr(client, "chat") and hasattr(client.chat, "completions"):
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": WEB_COPY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_instructions},
                ],
                temperature=0.5,
                max_tokens=2800,
            )
            html = resp.choices[0].message.content  # type: ignore[attr-defined]
        else:
            raise RuntimeError("OpenAI chat client not available.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    # If we have an image, inject a simple hero block right after <body>
    if image_b64:
        hero_block = f"""
        <header style="position:relative;overflow:hidden;">
          <img src="data:image/png;base64,{image_b64}" alt="Hero image" style="width:100%;height:auto;display:block;filter:contrast(1.05) saturate(1.05);" />
          <h1 style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:#fff;text-shadow:0 2px 12px rgba(0,0,0,.45);font-size:clamp(2rem,6vw,4rem);margin:0;padding:0 1rem;text-align:center;"></h1>
        </header>
        """
        # inject after first <body>
        lower = html.lower()
        idx = lower.find("<body")
        if idx != -1:
            # find the end of opening <body ...>
            closing = lower.find(">", idx)
            if closing != -1:
                html = html[: closing + 1] + hero_block + html[closing + 1 :]

    return html

def github_upsert_file(
    repo: str,
    branch: str,
    path: str,
    content_str: str,
    token: str,
    commit_message: str,
) -> None:
    """
    Create or update a file in a GitHub repo via the Contents API.
    """
    if not (repo and token):
        raise HTTPException(status_code=500, detail="GitHub repo/token not configured.")

    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}

    # Check if file exists to fetch its SHA
    sha = None
    r_get = requests.get(url, params={"ref": branch}, headers=headers, timeout=30)
    if r_get.status_code == 200:
        sha = r_get.json().get("sha")

    payload = {
        "message": commit_message,
        "content": base64.b64encode(content_str.encode("utf-8")).decode("utf-8"),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha

    r_put = requests.put(url, headers=headers, data=json.dumps(payload), timeout=60)
    if r_put.status_code not in (200, 201):
        raise HTTPException(
            status_code=500,
            detail=f"GitHub update failed: {r_put.status_code} {r_put.text}",
        )

def trigger_vercel_deploy(hook_url: str) -> None:
    if not hook_url:
        return
    try:
        r = requests.post(hook_url, timeout=30)
        if r.status_code not in (200, 201, 202):
            print(f"[vercel] non-200 from hook: {r.status_code} {r.text}")
    except Exception as e:
        print(f"[vercel] deploy hook error: {e}")

# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.get("/")
def root() -> Dict[str, str]:
    return {"ok": "SiteCraft backend running"}

@app.post("/generate-pure")
def generate_pure(req: GenReq) -> Dict[str, Any]:
    """
    Returns { html }
    """
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required.")

    img_b64 = generate_image_b64(req.prompt) if USE_IMAGE else None
    html = generate_html_copy(req.prompt, img_b64)
    return {"html": html}

@app.post("/publish")
def publish(req: PubReq) -> Dict[str, str]:
    """
    Generates HTML, commits to GitHub pages repo, triggers Vercel deploy hook,
    and returns { live_url }.
    """
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required.")

    img_b64 = generate_image_b64(req.prompt) if USE_IMAGE else None
    html = generate_html_copy(req.prompt, img_b64)

    # 1) Upsert index.html in repo
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    commit_msg = f"auto: publish SiteCraft page @ {timestamp}"
    github_upsert_file(
        repo=PAGES_REPO,
        branch=PAGES_BRANCH,
        path=PAGES_FILEPATH,
        content_str=html,
        token=GITHUB_TOKEN,
        commit_message=commit_msg,
    )

    # 2) Trigger Vercel
    if VERCEL_DEPLOY_HOOK_URL:
        trigger_vercel_deploy(VERCEL_DEPLOY_HOOK_URL)

    # 3) Return your live base URL (project domain)
    return {"live_url": LIVE_BASE_URL}

# -------------------------------------------------
# Run (for local debugging)
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
