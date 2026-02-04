import json
from openai import OpenAI
from app.config import Config
from app.models.meeting_model import Meeting

client = OpenAI(api_key=Config.OPENAI_API_KEY)


def generate_next_meeting_agenda(user_id: str, limit: int = 5):
    meetings = (
        Meeting.objects(user_id=user_id, status="completed")
        .order_by("-created_at")
        .limit(max(1, limit))
    )

    context_lines = []
    for m in meetings:
        context_lines.append(f"Title: {m.title}")
        if m.summary:
            context_lines.append(f"Summary: {m.summary}")
        if m.action_items:
            context_lines.append("Action Items: " + "; ".join(m.action_items))
        if m.key_decisions:
            context_lines.append("Key Decisions: " + "; ".join(m.key_decisions))
        context_lines.append("---")

    context = "\n".join(context_lines).strip()

    prompt = f"""
Bạn là trợ lý họp.

Dựa trên lịch sử cuộc họp dưới đây, hãy đề xuất agenda cho cuộc họp tiếp theo.
Trả về JSON gồm:
- agenda_items (list)
- goals (list)
- risks (list)
- follow_ups (list)

Lịch sử:
{context}
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    raw = res.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
    except Exception as e:
        raise ValueError(f"JSON parse failed: {e} | raw={raw}")

    return data
