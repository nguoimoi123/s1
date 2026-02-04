from ..models.reminder_model import Reminder
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional

class ReminderController:
    @staticmethod
    def create_reminder(user_id, title, remind_start, remind_end, location=None):
        reminder = Reminder(
            user_id=user_id,
            title=title,
            remind_start=remind_start,
            remind_end=remind_end,
            location=location
        )
        reminder.save()
        return {"id": str(reminder.id), "title": reminder.title}, 201
    
    @staticmethod
    def get_by_day(user_id, date, tz_offset_minutes=None):
        start_of_day = datetime.combine(date, time.min)
        end_of_day = datetime.combine(date, time.max)

        if tz_offset_minutes is not None:
            # Convert local day window to UTC window (stored as UTC)
            start_of_day = start_of_day - timedelta(minutes=tz_offset_minutes)
            end_of_day = end_of_day - timedelta(minutes=tz_offset_minutes)

        reminders = Reminder.objects(
            user_id=user_id,
            remind_start__gte=start_of_day,
            remind_start__lte=end_of_day
        )

        return [
            {
                "id": str(r.id),
                "title": r.title,
                "remind_start": r.remind_start.isoformat(),
                "remind_end": r.remind_end.isoformat(),
                "location": r.location,
                "done": r.done
            }
            for r in reminders
        ], 200
    def delete_reminder(reminder_id):
        reminder = Reminder.objects(id=reminder_id).first()
        if not reminder:
            return {"error": "Reminder not found"}, 404
        reminder.delete()
        return {"message": "Reminder deleted"}, 200

    @staticmethod
    def create_reminders_from_action_items(
        user_id: str,
        items: List[Dict[str, str]],
        default_start: Optional[datetime] = None,
        default_duration_minutes: int = 60,
    ):
        if not items:
            return [], 200

        created = []
        base_time = default_start or datetime.utcnow()

        for idx, item in enumerate(items):
            title = (item.get("title") or item.get("text") or "").strip()
            if not title:
                continue

            due_at = item.get("due_at")
            if due_at:
                try:
                    remind_start = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
                except Exception:
                    remind_start = base_time
            else:
                remind_start = base_time + timedelta(minutes=idx * 10)

            remind_end = remind_start + timedelta(minutes=default_duration_minutes)

            reminder = Reminder(
                user_id=user_id,
                title=title,
                remind_start=remind_start,
                remind_end=remind_end,
                location=item.get("location"),
            )
            reminder.save()
            created.append({"id": str(reminder.id), "title": reminder.title})

        return created, 201