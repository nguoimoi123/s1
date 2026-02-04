from datetime import datetime
from ..extensions import db

class Meeting(db.Document):
    """
    Model lưu trữ thông tin cuộc họp.
    Sử dụng sid từ Socket.IO làm primary key.
    """
    sid = db.StringField(primary_key=True, required=True)
    user_id = db.StringField(required=True)  # ID của user đang họp
    
    title = db.StringField(default="Untitled Meeting")
    status = db.StringField(default="in_progress") # in_progress, completed, error
    
    created_at = db.DateTimeField(default=datetime.utcnow)
    ended_at = db.DateTimeField()
    
    # Nội dung
    full_transcript = db.StringField() # Lưu toàn bộ văn bản
    speaker_names = db.DictField(default=dict)  # Map speakerId -> display name

    # Tags/labels
    tags = db.ListField(db.StringField(), default=list)
    
    # Kết quả AI
    summary = db.StringField()
    action_items = db.ListField(db.StringField())
    key_decisions = db.ListField(db.StringField())

    meta = {
        'collection': 'Meetings',
        'indexes': [
            'user_id',
            'created_at',
            'tags',
            {
                'fields': [
                    '$title',
                    '$summary',
                    '$full_transcript',
                    '$action_items',
                    '$key_decisions',
                ],
                'default_language': 'none',
            },
        ]
    }

    def to_dict(self):
        return {
            "id": self.sid,
            "title": self.title,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "participants": list(self.speaker_names.values()) if self.speaker_names else [],
            "summary": self.summary,
            "action_items": self.action_items,
            "key_decisions": self.key_decisions,
            "tags": self.tags or [],
        }