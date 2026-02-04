from flask_mongoengine import MongoEngine
from datetime import datetime
from ..extensions import db

class Folder(db.Document):
    user_id = db.StringField(required=True)
    name = db.StringField(required=True)
    description = db.StringField()
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'Folders',
        'indexes': [
            'user_id',
            {
                'fields': ['$name', '$description'],
                'default_language': 'none',
            },
        ],
    }
