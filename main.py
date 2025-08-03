from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import base64

# Initialize FastAPI app
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secure OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Request body model
class PromptRequest(BaseModel):
    prompt: str

# GitHub push function
def push_to_github(prompt: str, html_content: str):
    github_token = os.getenv("GITHUB_TOKEN")
    repo_name = "chehanvey/sitecraft-pages"
    file_path = "index.html"
    commit_message = f"Update: {prompt[:50]}..."

    g = Github(github_token)
    repo = g.get_repo(repo_name)

    try:
        # Check if file exists
        contents = repo.get_contents(file_path)
        repo.update_file(
            path=file_path,
            message=commit_message,
            content=html_content,
            sha=contents.sha,
            branch="main"
        )
    except Exception as e:
        # If file doesn't exist, create it
        repo.create_file(
            path=file_path,
            message=commit_message,
            content=html_content,
            branch="main"
        )

    return "https://sitecraft-pages.vercel.app"

@app.post("/generate-pure")
async def generate_pure_site(request: PromptRequest):
    prompt = request.prompt
    image_url = "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"

    # Step 1: Generate background image with DALL·E (no overlay text)
    try:
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=f"{prompt}, beautifully designed, professional background, no text allowed in the image generated, purely image only. All text is outside of generated image. image reflects user's prompt accurately",
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url"
        )
        image_url = image_response.data[0].url
    except Exception as e:
        print(f"Image generation failed: {e}")

    # Step 2: Generate full HTML layout with GPT-4
    try:
        html_response = openai.chat.completions.create(
            model="gpt-4",
            temperature=0.75,
            max_tokens=1800,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a highly creative and extremely talented web designer. Create a modern, responsive one-page HTML website with the following features:\n"
                        "- Full-width hero section background image based on users prompt. There is no text or wording allowed in the image except the title. Ensure spelling is correct.\n"
                        "- Website title is eye catching and contained in the hero. The title is to be creative. For example a garden centre called greenfinger could be written in green with trees or leaves. Title background blends visually with hero.\n"
                        "- Well-structured content sections relevant to the users prompt, with good spacing and relevant paragraphs. Each section should reflect the overall theme of the website.\n"
                        "- Visually distinct section backgrounds (soft colors or light gradients and section breakers).\n"
                        "- Borders between sections complimenting the website theme.\n"
                        "- Clear mobile-friendly layout using HTML + embedded CSS only.\n"
                        "- Add a simple footer.\n"
                        "Do NOT use lorem ipsum. Use plain placeholder headings and meaningful filler content relevant to the prompt.\n"
                        "Return only valid HTML."
                    )
                },
                {
                    "role": "user",
                    "content": f"Prompt: {prompt}\n\nUse this image for the hero background: {image_url}"
                }
            ]
        )
        html_code = html_response.choices[0].message.content.strip()
    except Exception as e:
        print(f"HTML generation failed: {e}")
        html_code = f"<h1>SiteCraft Error</h1><p>{e}</p>"

    # Push to GitHub Pages and get live site URL
    site_url = push_to_github(prompt, html_code)

    return { "html": html_code, "url": site_url }
