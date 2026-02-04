import secrets
from datetime import datetime
from typing import Dict, Optional
from ..models.user_model import User
from ..models.upgrade_code_model import UpgradeCode


PLAN_LIMITS: Dict[str, Dict[str, Optional[int]]] = {
    "free": {
        "meeting_limit": 10,
        "meeting_duration_minutes": 30,
        "folder_limit": 5,
        "files_per_folder_limit": 5,
        "qa_limit": 30,
        "ai_agent": 0,
        "in_meeting_ai": 0,
    },
    "plus": {
        "meeting_limit": 50,
        "meeting_duration_minutes": 240,  # 4 hours
        "folder_limit": 50,
        "files_per_folder_limit": 50,
        "qa_limit": 500,
        "ai_agent": 1,
        "in_meeting_ai": 0,
    },
    "premium": {
        "meeting_limit": None,
        "meeting_duration_minutes": None,
        "folder_limit": None,
        "files_per_folder_limit": None,
        "qa_limit": None,
        "ai_agent": 1,
        "in_meeting_ai": 1,
    },
}


def get_plan_limits(plan: str) -> Dict[str, Optional[int]]:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


def get_user_plan(user_id: str) -> str:
    user = User.objects(id=user_id).first()
    return user.plan if user and user.plan else "free"


def generate_upgrade_code(plan: str) -> str:
    if plan not in ("plus", "premium"):
        raise ValueError("Invalid plan")
    raw = secrets.token_urlsafe(8).replace("-", "").replace("_", "")
    return f"{plan[:2].upper()}-{raw[:10]}"


def create_upgrade_codes(plan: str, count: int = 1):
    codes = []
    for _ in range(max(1, count)):
        code_value = generate_upgrade_code(plan)
        code = UpgradeCode(code=code_value, plan=plan)
        code.save()
        codes.append(code)
    return codes


def ensure_default_upgrade_codes(plus_count: int = 10, premium_count: int = 10):
    created = {"plus": [], "premium": []}

    if UpgradeCode.objects(plan="plus").count() < plus_count:
        to_create = plus_count - UpgradeCode.objects(plan="plus").count()
        created["plus"] = create_upgrade_codes("plus", to_create)

    if UpgradeCode.objects(plan="premium").count() < premium_count:
        to_create = premium_count - UpgradeCode.objects(plan="premium").count()
        created["premium"] = create_upgrade_codes("premium", to_create)

    return {
        "plus": [c.code for c in created["plus"]],
        "premium": [c.code for c in created["premium"]],
    }


def redeem_upgrade_code(user_id: str, code_value: str):
    code = UpgradeCode.objects(code=code_value, is_active=True).first()
    if not code:
        return None, "Invalid or used code"

    user = User.objects(id=user_id).first()
    if not user:
        return None, "User not found"

    user.plan = code.plan
    user.save()

    code.is_active = False
    code.used_by = str(user.id)
    code.used_at = datetime.utcnow()
    code.save()

    return user, None
