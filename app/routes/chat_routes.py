from flask import Blueprint, request, jsonify
from app.services.rag_service import retrieve_relevant_chunks
from openai import OpenAI
from app.config import Config
from app.models.meeting_model import Meeting # Import Meeting model để lấy transcript gốc

bp = Blueprint("chatm", __name__, url_prefix="/chat")
client = OpenAI(api_key=Config.OPENAI_API_KEY)

@bp.route("/meeting", methods=["POST"])
def chat_with_meeting():
    """
    API Chat với nội dung cuộc họp sử dụng RAG + Fallback.
    """
    data = request.get_json()
    query = data.get("query")
    sid = data.get("sid") 
    user_id = data.get("user_id", "default_user")

    if not query or not sid:
        return jsonify({"error": "Missing query or sid"}), 400

    # 1. Thử tìm kiếm thông tin từ RAG (CSDL Vector)
    relevant_chunks = retrieve_relevant_chunks(user_id, query, top_k=3, folder_id=sid)
    
    context_text = ""
    source_type = "RAG" # Để debug xem nguồn nào đang trả lời

    # 2. Nếu RAG chưa có dữ liệu (vì vừa mới tạo hoặc lỗi), ta dùng Fallback
    if not relevant_chunks:
        # Lấy transcript gốc từ bảng Meeting
        meeting = Meeting.objects(sid=sid).first()
        
        if meeting and meeting.full_transcript:
            # Cắt bớt transcript nếu quá dài để tránh tràn token (lấy tối đa 4000 ký tự)
            raw_transcript = meeting.full_transcript
            if len(raw_transcript) > 4000:
                raw_transcript = raw_transcript[:4000] + "..."
            
            context_text = f"Đây là nội dung cuộc họp chưa được index đầy đủ:\n{raw_transcript}"
            source_type = "RAW_TRANSCRIPT"
        else:
            context_text = "Không tìm thấy thông tin về cuộc họp này."
            source_type = "NONE"
    else:
        # Nếu có RAG thì dùng (chuẩn nhất)
        context_text = "\n".join([c.text for c in relevant_chunks])

    # 3. Tạo prompt cho AI
    system_prompt = f"""
    Bạn là trợ lý họp thông minh của MeetingMind.
    
    Dữ liệu nguồn: {source_type}
    
    --- CONTEXT (Thông tin cuộc họp) ---
    {context_text}
    --- END CONTEXT ---
    
    Nhiệm vụ: Trả lời câu hỏi của người dùng dựa trên CONTEXT trên.
    Câu hỏi: {query}
    
    Nếu trong context không có thông tin, hãy trả lời: "Xin lỗi, tôi không tìm thấy thông tin này trong nội dung cuộc họp."
    """

    try:
        # 4. Gọi OpenAI
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Bạn là trợ lý hữu ích, trả lời ngắn gọn súc tích."},
                {"role": "user", "content": system_prompt}
            ],
            temperature=0.5
        )
        
        answer = response.choices[0].message.content.strip()
        return jsonify({"answer": answer, "source": source_type})

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({"error": str(e)}), 500