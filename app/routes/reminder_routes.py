from flask import Blueprint, request, jsonify
from datetime import datetime
from app.services.reminder_service import ReminderController

reminder_bp = Blueprint("reminder", __name__, url_prefix="/reminder")


@reminder_bp.route('/add', methods=['POST'])
def create_reminder():
    data = request.get_json()
    user_id = data.get('user_id')
    title = data.get('title')
    location = data.get('location')

    try:
        remind_start = datetime.fromisoformat(
            data.get('remind_start').replace("Z", "+00:00")
        )
        remind_end = datetime.fromisoformat(
            data.get('remind_end').replace("Z", "+00:00")
        )
    except Exception:
        return jsonify({"error": "Invalid datetime format"}), 400

    result, status_code = ReminderController.create_reminder(
        user_id=user_id,
        title=title,
        remind_start=remind_start,
        remind_end=remind_end,
        location=location
    )
    return jsonify(result), status_code

@reminder_bp.route('/day', methods=['GET'])
def get_reminder_by_day():
    user_id = request.args.get('user_id')
    date_str = request.args.get('date')
    tz_offset = request.args.get('tz_offset')

    if not user_id or not date_str:
        return {"error": "user_id and date are required"}, 400

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid date format (YYYY-MM-DD)"}, 400

    try:
        offset_minutes = int(tz_offset) if tz_offset is not None else None
    except Exception:
        offset_minutes = None

    return ReminderController.get_by_day(user_id, date, offset_minutes)

@reminder_bp.route('/delete/<reminder_id>', methods=['DELETE'])
def delete_reminder(reminder_id):
    return ReminderController.delete_reminder(reminder_id)