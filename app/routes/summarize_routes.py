from flask import Blueprint, jsonify, request
from app.services.openai_service import summarize_transcript
from app.services.meeting_service import get_or_create_meeting, save_summary, apply_speaker_names
from app.models.meeting_model import Meeting
from app.services.rag_service import ingest_meeting_transcript
from app.services.reminder_service import ReminderController

bp = Blueprint("summarize", __name__)

@bp.route("/summarize/<sid>", methods=["GET"])
def summarize_sid(sid):
    # Lấy user_id từ query params, ưu tiên user_id của meeting nếu có
    user_id = request.args.get('user_id')

    meeting = Meeting.objects(sid=sid).first()
    if meeting:
        if not user_id or user_id == 'default_user':
            user_id = meeting.user_id
    else:
        if not user_id:
            user_id = 'default_user'
        meeting = get_or_create_meeting(sid, user_id)
    
    # Kiểm tra xem đã có transcript trong DB chưa
    if not meeting.full_transcript:
        return jsonify({"error": "No transcript found in database"}), 400

    # Áp dụng mapping tên người nói (nếu có)
    updated_transcript = apply_speaker_names(meeting.full_transcript, meeting.speaker_names)

    # Nếu đã có summary rồi thì trả về luôn (tránh tính phí OpenAI lại)
    if meeting.summary:
        return jsonify({
            "summary": meeting.summary,
            "action_items": meeting.action_items,
            "key_decisions": meeting.key_decisions,
            "full_transcript": updated_transcript
        })

    # 2. Gọi OpenAI để tóm tắt
    try:
        data = summarize_transcript(updated_transcript)
        
        # 3. Lưu kết quả vào Meeting DB
        save_summary(sid, data)
        
        # 4. BẮT ĐẦU RAG: Ingest dữ liệu vào bảng Chunks để dùng cho Chat sau này
        # Chạy ngầm hoặc trực tiếp tùy độ dài transcript
        ingest_meeting_transcript(sid, user_id, updated_transcript)
        
        # 5. Optionally create tasks from action items
        create_tasks = request.args.get("create_tasks", "false").lower() == "true"
        if create_tasks and data.get("action_items"):
            items = [{"title": x} for x in data.get("action_items")]
            ReminderController.create_reminders_from_action_items(
                user_id=user_id,
                items=items,
            )

        return jsonify({
            "summary": data.get("summary", ""),
            "action_items": data.get("action_items", []),
            "key_decisions": data.get("key_decisions", []),
            "full_transcript": updated_transcript
        })
    except Exception as e:
        print(f"Error summarizing: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/summarize", methods=["POST"])
def summarize_post():
    body = request.get_json()
    transcript = body.get("transcript", "").strip()
    if not transcript:
        return jsonify({"error": "No transcript"}), 400

    data = summarize_transcript(transcript)
    return jsonify({
        "summary": data.get("summary", ""),
        "action_items": data.get("action_items", []),
        "key_decisions": data.get("key_decisions", []),
        "full_transcript": transcript
    })