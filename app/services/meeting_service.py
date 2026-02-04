from datetime import datetime
import re
from app.models.chunk_model import Chunk

from ..models.meeting_model import Meeting
from mongoengine.errors import NotUniqueError

def get_or_create_meeting(sid, user_id, title=None):
    """
    Lấy cuộc họp nếu đã có, nếu chưa thì tạo mới.
    Được gọi ngay khi bắt đầu Socket kết nối.
    """
    try:
        Meeting.objects(sid=sid).update_one(
            set_on_insert__sid=sid,
            set_on_insert__user_id=user_id,
            set_on_insert__status="in_progress",
            set_on_insert__title=title or "Untitled Meeting",
            upsert=True,
        )
    except NotUniqueError:
        pass

    meeting = Meeting.objects(sid=sid).first()
    if meeting and title and title != meeting.title:
        meeting.title = title
        meeting.save()
    return meeting

def append_transcript(sid, text):
    """
    Nối thêm câu mới vào full_transcript của cuộc họp.
    Gọi khi có kết quả chép lời hoàn chỉnh.
    """
    meeting = Meeting.objects(sid=sid).first()
    if meeting:
        if meeting.speaker_names:
            text = apply_speaker_names(text, meeting.speaker_names)
        if meeting.full_transcript:
            meeting.full_transcript += "\n" + text
        else:
            meeting.full_transcript = text
        meeting.save()

def save_summary(sid, summary_data):
    """
    Lưu kết quả tóm tắt sau khi họp xong.
    Cập nhật status thành 'completed'.
    """
    meeting = Meeting.objects(sid=sid).first()
    if meeting:
        meeting.status = "completed"
        meeting.ended_at = datetime.utcnow()
        meeting.summary = summary_data.get("summary")
        meeting.action_items = summary_data.get("action_items", [])
        meeting.key_decisions = summary_data.get("key_decisions", [])
        
        # Nếu chưa có transcript (do lỗi gì đó), lấy từ data trả về
        if not meeting.full_transcript:
            meeting.full_transcript = summary_data.get("full_transcript")
            
        meeting.save()
    return meeting

def get_user_meetings(user_id):
    """
    Lấy danh sách cuộc họp của 1 user, sắp xếp theo thời gian mới nhất.
    """
    return Meeting.objects(user_id=user_id).order_by('-created_at')


def update_meeting_meta(sid, title=None, user_id=None):
    meeting = Meeting.objects(sid=sid).first()
    if not meeting:
        if not user_id:
            return None
        meeting = Meeting(
            sid=sid,
            user_id=user_id,
            status="in_progress",
            title=title or "Untitled Meeting",
        )
        meeting.save()
        return meeting

    if title:
        meeting.title = title

    meeting.save()
    return meeting


def update_speaker_name(sid, speaker_id, name):
    meeting = Meeting.objects(sid=sid).first()
    if not meeting:
        return None

    if meeting.speaker_names is None:
        meeting.speaker_names = {}

    meeting.speaker_names[speaker_id] = name
    meeting.save()
    return meeting


def apply_speaker_names(transcript, speaker_names):
    if not transcript or not speaker_names:
        return transcript

    updated = transcript
    for speaker_id, name in speaker_names.items():
        if not name:
            continue
        # Replace both raw speaker_id and prefixed "Người {speaker_id}"
        candidates = {speaker_id}
        if not str(speaker_id).startswith("Người "):
            candidates.add(f"Người {speaker_id}")

        for candidate in candidates:
            pattern = re.compile(rf"(?m)^{re.escape(candidate)}\s*:")
            updated = pattern.sub(f"{name}:", updated)
    return updated
def delete_meeting_by_sid(sid):
    meeting = Meeting.objects(sid=sid).first()
    if not meeting:
        return False

    meeting.delete()
    Chunk.objects(folder_id=sid).delete()
    return True