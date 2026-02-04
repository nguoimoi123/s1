from datetime import datetime, timedelta
from ..extensions import db


class TeamInvite(db.Document):
    team_id = db.StringField(required=True)
    email = db.StringField(required=True)
    token = db.StringField(required=True, unique=True)
    invited_by = db.StringField(required=True)
    status = db.StringField(default="invited")  # invited/accepted/expired
    created_at = db.DateTimeField(default=datetime.utcnow)
    expires_at = db.DateTimeField(default=lambda: datetime.utcnow() + timedelta(days=7))

    meta = {
        'collection': 'TeamInvites',
        'indexes': ['team_id', 'email', 'token', 'status', 'expires_at']
    }
