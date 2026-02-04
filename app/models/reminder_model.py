from flask_mongoengine import MongoEngine
from datetime import datetime
from ..extensions import db

class Reminder(db.Document):
    user_id = db.StringField(required=True)

    title = db.StringField(required=True)

    remind_start = db.DateTimeField(required=True)

    remind_end = db.DateTimeField(required=True)

    location = db.StringField()
    
    done = db.BooleanField(default=False)

    meta = {'collection': 'Reminders'}