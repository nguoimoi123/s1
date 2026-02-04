from flask import Blueprint, request, jsonify
from datetime import datetime
from app.services.meeting_service import get_user_meetings, update_meeting_meta
from app.services.reminder_service import ReminderController
from app.services.agenda_service import generate_next_meeting_agenda
from app.models.meeting_model import Meeting
from app.models.chunk_model import Chunk

meeting_bp = Blueprint("meetings", __name__, url_prefix="/meetings")

@meeting_bp.route("/", methods=["GET"])
def list_meetings():
    """
    API lấy danh sách cuộc họp.
    Param: user_id (string)
    """
    user_id = request.args.get('user_id')
    tag = request.args.get('tag')
    
    if not user_id:
        return jsonify({"error": "Missing user_id parameter"}), 400

    try:
        meetings = get_user_meetings(user_id)
        if tag:
            meetings = meetings.filter(tags__in=[tag])
        # Convert list object sang JSON
        result = [m.to_dict() for m in meetings]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@meeting_bp.route("/<sid>", methods=["DELETE"])
def delete_meeting(sid):
    """
    Xóa cuộc họp và toàn bộ dữ liệu liên quan (RAG chunks).
    """
    try:
        # 1. Xóa bản ghi Meeting
        meeting = Meeting.objects(sid=sid).first()
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
        
        meeting.delete()

        # 2. Xóa các Chunks liên quan (RAG) trong bảng Chunks
        # (Trong model chunk_model ta dùng folder_id để lưu sid của meeting)
        deleted_chunks = Chunk.objects(folder_id=sid).delete()
        print(f"Deleted {deleted_chunks} chunks for meeting {sid}")

        return jsonify({"message": "Meeting deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting meeting: {e}")
        return jsonify({"error": str(e)}), 500


@meeting_bp.route("/<sid>", methods=["PUT"])
def update_meeting(sid):
    """
    Cập nhật thông tin cuộc họp (hiện tại hỗ trợ đổi title).
    Body: { "title": "My Meeting" }
    """
    data = request.get_json() or {}
    title = data.get("title")
    user_id = data.get("user_id") or request.args.get("user_id")

    if not title:
        return jsonify({"error": "Missing title"}), 400

    try:
        meeting = update_meeting_meta(sid, title=title, user_id=user_id)
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
        return jsonify(meeting.to_dict()), 200
    except Exception as e:
        print(f"Error updating meeting: {e}")
        return jsonify({"error": str(e)}), 500


@meeting_bp.route("/<sid>/tags", methods=["PUT"])
def update_meeting_tags(sid):
    data = request.get_json() or {}
    tags = data.get("tags")
    if tags is None or not isinstance(tags, list):
        return jsonify({"error": "tags must be a list"}), 400

    try:
        meeting = Meeting.objects(sid=sid).first()
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
        meeting.tags = [str(t).strip() for t in tags if str(t).strip()]
        meeting.save()
        return jsonify({"id": meeting.sid, "tags": meeting.tags}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@meeting_bp.route("/<sid>/speakers", methods=["PUT"])
def update_speaker_mapping(sid):
    data = request.get_json() or {}
    speaker_names = data.get("speaker_names")
    speaker_id = data.get("speaker_id")
    name = data.get("name")

    if speaker_names is None and (not speaker_id or not name):
        return jsonify({"error": "speaker_names or speaker_id/name required"}), 400

    try:
        meeting = Meeting.objects(sid=sid).first()
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404

        if speaker_names is None:
            speaker_names = {speaker_id: name}

        if meeting.speaker_names is None:
            meeting.speaker_names = {}

        for k, v in speaker_names.items():
            if not k or not v:
                continue
            meeting.speaker_names[str(k)] = str(v)

        meeting.save()
        return jsonify({"id": meeting.sid, "speaker_names": meeting.speaker_names}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@meeting_bp.route("/<sid>/action-items/to-tasks", methods=["POST"])
def action_items_to_tasks(sid):
    data = request.get_json() or {}
    user_id = data.get("user_id") or request.args.get("user_id")
    items = data.get("items")
    default_start = data.get("default_start")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    meeting = Meeting.objects(sid=sid).first()
    if not meeting:
        return jsonify({"error": "Meeting not found"}), 404

    if items is None:
        items = [{"title": x} for x in (meeting.action_items or [])]

    if default_start:
        try:
            default_start_dt = datetime.fromisoformat(default_start.replace("Z", "+00:00"))
        except Exception:
            default_start_dt = None
    else:
        default_start_dt = None

    created, status = ReminderController.create_reminders_from_action_items(
        user_id=user_id,
        items=items,
        default_start=default_start_dt,
    )

    return jsonify({"created": created, "count": len(created)}), status


@meeting_bp.route("/agenda/next", methods=["GET"])
def get_next_agenda():
    user_id = request.args.get("user_id")
    limit = int(request.args.get("limit", 5))
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        data = generate_next_meeting_agenda(user_id=user_id, limit=limit)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@meeting_bp.route("/<sid>", methods=["GET"])
def get_meeting_detail(sid):
    try:
        meeting = Meeting.objects(sid=sid).first()
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404

        data = meeting.to_dict()
        data["speaker_names"] = meeting.speaker_names or {}
        data["tags"] = meeting.tags or []
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500