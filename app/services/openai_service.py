import json
from openai import OpenAI
from app.config import Config

client = OpenAI(api_key=Config.OPENAI_API_KEY)

def summarize_transcript(transcript: str):
    prompt = f"""
Bạn là trợ lý họp.

Từ transcript sau, hãy trả về JSON gồm:
- summary
- action_items (list)
- key_decisions (list)

Transcript:
{transcript}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    raw = res.choices[0].message.content.strip()

    if not raw:
        raise ValueError("OpenAI returned empty content")

    # Nếu AI bọc JSON trong ```json ... ```
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
    except Exception as e:
        raise ValueError(f"JSON parse failed: {e} | raw={raw}")

    return data
