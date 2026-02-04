from datetime import datetime
from ..models.user_model import User
from ..models.meeting_model import Meeting
from ..services.plan_service import get_plan_limits, get_user_plan


def _month_key():
    return datetime.utcnow().strftime("%Y%m")


def _ensure_month(user: User):
    key = _month_key()
    if user.qa_month != key:
        user.qa_month = key
        user.qa_used = 0
        user.save()


def get_usage(user_id: str):
    user = User.objects(id=user_id).first()
    if not user:
        return None, "User not found"

    _ensure_month(user)

    plan = get_user_plan(user_id)
    limits = get_plan_limits(plan)

    qa_limit = limits.get("qa_limit")
    qa_remaining = None if qa_limit is None else max(0, qa_limit - user.qa_used)

    meeting_limit = limits.get("meeting_limit")
    meetings_used = Meeting.objects(user_id=user_id).count()
    meetings_remaining = None
    if meeting_limit is not None:
        meetings_remaining = max(0, meeting_limit - meetings_used)

    return {
        "plan": plan,
        "limits": limits,
        "qa_used": user.qa_used,
        "qa_remaining": qa_remaining,
        "meetings_used": meetings_used,
        "meetings_remaining": meetings_remaining,
    }, None


def check_and_increment_qa(user_id: str):
    user = User.objects(id=user_id).first()
    if not user:
        return False, "User not found"

    _ensure_month(user)

    plan = get_user_plan(user_id)
    limits = get_plan_limits(plan)
    qa_limit = limits.get("qa_limit")

    if qa_limit is not None and user.qa_used >= qa_limit:
        return False, "Q&A limit reached"

    user.qa_used += 1
    user.save()
    return True, None
