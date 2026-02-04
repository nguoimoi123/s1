from datetime import datetime
from ..extensions import db


class TeamMember(db.Document):
    team_id = db.StringField(required=True)
    user_id = db.StringField(required=True)
    role = db.StringField(default='member')  # owner/member
    status = db.StringField(default='invited')  # invited/active
    joined_at = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'TeamMembers',
        'indexes': ['team_id', 'user_id', 'status']
    }
