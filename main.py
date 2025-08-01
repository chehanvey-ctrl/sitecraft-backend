from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
from jinja2 import Template

app = FastAPI()

# ✅ CORS setup for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sitecraft-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

class PromptRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_site(request: PromptRequest):
    prompt = request.prompt

    # ✅ Use Unsplash fallback image (reliable)
    image_url = "https://source.unsplash.com/1024x1024/?technology,website"

    # Uncomment below if/when we want to test DALL·E again
    """
    try:
        image_response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
            response_format="url"
        )
        image_url = image_response.data[0].url
    except Exception as e:
        print("❌ DALL·E failed, using fallback:", e)
    """

    # ✅ Template selection logic
    template_name = "template1.html"
    if "business" in prompt.lower():
        template_name = "template2.html"
    elif "portfolio" in prompt.lower():
        template_name = "template3.html"
    elif "blog" in prompt.lower():
        template_name = "template4.html"
    elif "ecommerce" in prompt.lower():
        template_name = "template5.html"

    # ✅ Render HTML from template
    try:
        with open(template_name, "r") as file:
            template = Template(file.read())
        html_code = template.render(image_url=image_url, prompt=prompt)
        return { "html": html_code }
    except Exception as e:
        return { "html": f"<h1>❌ Template error: {str(e)}</h1>" }
