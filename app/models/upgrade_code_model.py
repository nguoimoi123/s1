from datetime import datetime
from ..extensions import db


class UpgradeCode(db.Document):
    code = db.StringField(required=True, unique=True)
    plan = db.StringField(required=True, choices=["plus", "premium"])
    is_active = db.BooleanField(default=True)
    used_by = db.StringField()
    used_at = db.DateTimeField()
    created_at = db.DateTimeField(default=datetime.utcnow)

    meta = {"collection": "UpgradeCodes"}
