@app.post("/generate")
async def generate(request: PromptRequest):
    prompt = request.prompt

    system_prompt = (
        "You are a web design AI assistant. Based on the user's description, "
        "generate a full HTML5 website. Do not include explanations or markdown. "
        "Only return pure, valid HTML with embedded CSS styles. "
        "The design should be clean, modern, and mobile responsive."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    html_code = response.choices[0].message.content.strip()
    return JSONResponse(content={"html": html_code})
