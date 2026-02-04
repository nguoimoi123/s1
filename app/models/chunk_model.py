from flask_mongoengine import MongoEngine
from datetime import datetime
from ..extensions import db

class Chunk(db.Document):
    user_id = db.StringField(required=True)

    folder_id = db.StringField(required=True)

    file_id = db.StringField(required=True)

    chunk_index = db.IntField(required=True)

    text = db.StringField(required=True)

    embedding = db.ListField(db.FloatField(), required=True)

    created_at = db.DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'Chunks'}
