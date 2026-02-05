import eventlet
from eventlet.queue import Queue
from flask import request
from flask_socketio import emit
from app.extensions import socketio
from app.services.speechmatics_service import sm_worker
from app.services.meeting_service import get_or_create_meeting, update_speaker_name
from app.services.plan_service import get_plan_limits, get_user_plan
from app.models.meeting_model import Meeting

# Dictionary lưu queue cho từng sid active
audio_queues = {}

@socketio.on("start_streaming")
def start_streaming(data=None):
    sid = request.sid

    user_id = None
    if isinstance(data, dict):
        user_id = data.get("user_id")
    if not user_id:
        user_id = request.args.get("user_id")
    if not user_id:
        user_id = "default_user"

    plan = get_user_plan(user_id)
    limits = get_plan_limits(plan)
    meeting_limit = limits.get("meeting_limit")

    if meeting_limit is not None:
        current_count = Meeting.objects(user_id=user_id).count()
        if current_count >= meeting_limit:
            emit("status", {
                "msg": "Meeting limit reached for current plan",
                "plan": plan,
                "limit": meeting_limit,
            })
            return

    title = None
    if isinstance(data, dict):
        title = data.get("title")
    get_or_create_meeting(sid, user_id, title=title)

    # ✅ Dùng Queue của eventlet
    audio_queues[sid] = Queue()

    # ✅ Chạy worker bằng green thread
    eventlet.spawn_n(sm_worker, sid, audio_queues[sid])

    emit("status", {"msg": "Speechmatics ready"})


@socketio.on("audio_data")
def audio_data(data):
    sid = request.sid
    if sid in audio_queues and len(data) > 5:
        audio_queues[sid].put(data[5:])


@socketio.on("end_meeting")
def end_meeting():
    sid = request.sid
    if sid in audio_queues:
        audio_queues[sid].put(None)


@socketio.on("set_speaker_name")
def set_speaker_name(data=None):
    sid = request.sid
    if not isinstance(data, dict):
        return

    speaker_id = data.get("speaker_id")
    name = data.get("name")

    if not speaker_id or not name:
        return

    update_speaker_name(sid, speaker_id, name)


@socketio.on("disconnect")
def disconnect():
    audio_queues.pop(request.sid, None)
