from datetime import datetime
from ..extensions import db

class User(db.Document):
    email = db.StringField(required=True, unique=True)
    name = db.StringField(required=True)
    password = db.StringField(default="")  # Cho Google login, password trống
    avatar = db.StringField()
    plan = db.StringField(default="free")
    qa_used = db.IntField(default=0)
    qa_month = db.StringField(default="")
    created_at = db.DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'Users'}
