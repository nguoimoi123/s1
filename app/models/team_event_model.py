from datetime import datetime
from ..extensions import db


class TeamEvent(db.Document):
    team_id = db.StringField(required=True)
    created_by = db.StringField(required=True)
    title = db.StringField(required=True)
    start_time = db.DateTimeField(required=True)
    end_time = db.DateTimeField(required=True)
    location = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'TeamEvents',
        'indexes': ['team_id', 'created_by', 'start_time']
    }
