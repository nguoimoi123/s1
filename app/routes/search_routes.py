from flask import Blueprint, request, jsonify
from app.models.meeting_model import Meeting
from app.models.folder_model import Folder
from app.models.file_model import File

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("", methods=["GET"])
def search_all():
    user_id = request.args.get("user_id")
    query = (request.args.get("q") or "").strip()
    limit = int(request.args.get("limit", 20))

    if not user_id or not query:
        return jsonify({"error": "user_id and q are required"}), 400

    q = query

    def _text_search(collection, match_filter, limit_count):
        pipeline = [
            {"$match": match_filter},
            {"$addFields": {"score": {"$meta": "textScore"}}},
            {"$sort": {"score": -1}},
            {"$limit": limit_count},
        ]
        return list(collection.aggregate(pipeline))

    try:
        meetings_raw = _text_search(
            Meeting._get_collection(),
            {"user_id": user_id, "$text": {"$search": q}},
            limit,
        )
    except Exception:
        meetings_raw = list(
            Meeting.objects(user_id=user_id).filter(
                __raw__={
                    "$or": [
                        {"title": {"$regex": q, "$options": "i"}},
                        {"summary": {"$regex": q, "$options": "i"}},
                        {"full_transcript": {"$regex": q, "$options": "i"}},
                        {"action_items": {"$regex": q, "$options": "i"}},
                        {"key_decisions": {"$regex": q, "$options": "i"}},
                    ]
                }
            )[:limit]
        )

    try:
        folders_raw = _text_search(
            Folder._get_collection(),
            {"user_id": user_id, "$text": {"$search": q}},
            limit,
        )
    except Exception:
        folders_raw = list(
            Folder.objects(user_id=user_id).filter(
                __raw__={
                    "$or": [
                        {"name": {"$regex": q, "$options": "i"}},
                        {"description": {"$regex": q, "$options": "i"}},
                    ]
                }
            )[:limit]
        )

    try:
        files_raw = _text_search(
            File._get_collection(),
            {"user_id": user_id, "$text": {"$search": q}},
            limit,
        )
    except Exception:
        files_raw = list(
            File.objects(user_id=user_id).filter(
                __raw__={
                    "$or": [
                        {"filename": {"$regex": q, "$options": "i"}},
                        {"content": {"$regex": q, "$options": "i"}},
                    ]
                }
            )[:limit]
        )

    meetings = []
    for m in meetings_raw:
        if hasattr(m, "sid"):
            meetings.append({
                "type": "meeting",
                "id": m.sid,
                "title": m.title,
                "created_at": m.created_at.isoformat(),
                "summary": m.summary,
                "tags": m.tags or [],
            })
        else:
            created_at = m.get("created_at")
            created_at_val = created_at.isoformat() if hasattr(created_at, "isoformat") else created_at
            meetings.append({
                "type": "meeting",
                "id": m.get("_id"),
                "title": m.get("title"),
                "created_at": created_at_val,
                "summary": m.get("summary"),
                "tags": m.get("tags") or [],
            })

    folders = []
    for f in folders_raw:
        if hasattr(f, "id"):
            folders.append({
                "type": "notebook",
                "id": str(f.id),
                "title": f.name,
                "description": f.description,
                "created_at": f.created_at.isoformat(),
            })
        else:
            created_at = f.get("created_at")
            created_at_val = created_at.isoformat() if hasattr(created_at, "isoformat") else created_at
            folders.append({
                "type": "notebook",
                "id": str(f.get("_id")),
                "title": f.get("name"),
                "description": f.get("description"),
                "created_at": created_at_val,
            })

    files = []
    for f in files_raw:
        if hasattr(f, "id"):
            files.append({
                "type": "file",
                "id": str(f.id),
                "title": f.filename,
                "folder_id": f.folder_id,
            })
        else:
            files.append({
                "type": "file",
                "id": str(f.get("_id")),
                "title": f.get("filename"),
                "folder_id": f.get("folder_id"),
            })

    return jsonify({
        "query": query,
        "meetings": meetings,
        "notebooks": folders,
        "files": files,
    }), 200
