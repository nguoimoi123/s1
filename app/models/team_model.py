from datetime import datetime
from ..extensions import db


class Team(db.Document):
    name = db.StringField(required=True)
    owner_id = db.StringField(required=True)
    created_at = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'Teams',
        'indexes': ['owner_id', 'created_at']
    }
