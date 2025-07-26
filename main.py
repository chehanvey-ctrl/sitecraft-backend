from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import os
from openai import OpenAI

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.post("/generate")
async def generate(request: Request):
    data = await request.json()
    prompt = data.get("prompt")
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    html_code = response.choices[0].message.content
    return JSONResponse(content={"html": html_code})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
