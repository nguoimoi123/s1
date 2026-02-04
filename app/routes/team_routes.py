from flask import Blueprint, request, jsonify
from datetime import datetime
from app.services.team_service import (
    create_team,
    list_user_teams,
    list_team_members,
    invite_member,
    accept_invite,
    create_team_event,
    list_user_invites,
    remove_member,
    delete_team,
    accept_invite_by_token,
)
from app.models.team_event_model import TeamEvent

team_bp = Blueprint("teams", __name__, url_prefix="/teams")


@team_bp.route("/create", methods=["POST"])
def create_team_route():
    data = request.get_json() or {}
    owner_id = data.get("owner_id")
    name = data.get("name")

    if not owner_id or not name:
        return jsonify({"error": "owner_id and name are required"}), 400

    team, error = create_team(owner_id=owner_id, name=name)
    if error:
        return jsonify({"error": error}), 403

    return jsonify({"id": str(team.id), "name": team.name, "owner_id": team.owner_id}), 201


@team_bp.route("", methods=["GET"])
def list_teams_route():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    teams = list_user_teams(user_id)
    return jsonify([
        {
            "id": str(t.id),
            "name": t.name,
            "owner_id": t.owner_id,
            "created_at": t.created_at.isoformat(),
        }
        for t in teams
    ]), 200


@team_bp.route("/<team_id>/members", methods=["GET"])
def list_members_route(team_id):
    members = list_team_members(team_id)
    return jsonify([
        {
            "user_id": m.user_id,
            "role": m.role,
            "status": m.status,
        }
        for m in members
    ]), 200


@team_bp.route("/<team_id>/invite", methods=["POST"])
def invite_member_route(team_id):
    data = request.get_json() or {}
    owner_id = data.get("owner_id")
    member_id = data.get("member_id")
    member_email = data.get("member_email")

    if not owner_id or (not member_id and not member_email):
        return jsonify({"error": "owner_id and member_id/member_email are required"}), 400

    member, error = invite_member(
        team_id=team_id,
        owner_id=owner_id,
        member_id=member_id,
        member_email=member_email,
    )
    if error:
        return jsonify({"error": error}), 403

    return jsonify({
        "team_id": team_id,
        "member_id": member.user_id,
        "status": member.status,
    }), 200


@team_bp.route("/invites", methods=["GET"])
def list_invites_route():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    invites = list_user_invites(user_id)
    return jsonify(invites), 200


@team_bp.route("/<team_id>/accept", methods=["POST"])
def accept_invite_route(team_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    member, error, plan_changed, plan = accept_invite(team_id=team_id, user_id=user_id)
    if error:
        return jsonify({"error": error}), 403

    return jsonify({
        "team_id": team_id,
        "user_id": member.user_id,
        "status": member.status,
        "plan_changed": plan_changed,
        "plan": plan,
    }), 200


@team_bp.route("/invites/accept", methods=["POST"])
def accept_invite_by_token_route():
    data = request.get_json() or {}
    token = data.get("token")
    user_id = data.get("user_id")
    email = data.get("email")

    if not token:
        return jsonify({"error": "token is required"}), 400

    result, error = accept_invite_by_token(token=token, user_id=user_id, email=email)
    if error:
        return jsonify({"error": error}), 403

    return jsonify(result), 200


@team_bp.route("/<team_id>/events", methods=["POST"])
def create_team_event_route(team_id):
    data = request.get_json() or {}
    creator_id = data.get("creator_id")
    title = data.get("title")
    location = data.get("location")

    if not creator_id or not title:
        return jsonify({"error": "creator_id and title are required"}), 400

    try:
        start_time = datetime.fromisoformat(data.get("start_time").replace("Z", "+00:00"))
        end_time = datetime.fromisoformat(data.get("end_time").replace("Z", "+00:00"))
    except Exception:
        return jsonify({"error": "Invalid datetime format"}), 400

    event, error = create_team_event(
        team_id=team_id,
        creator_id=creator_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        location=location,
    )

    if error:
        return jsonify({"error": error}), 403

    return jsonify({
        "id": str(event.id),
        "team_id": team_id,
        "title": event.title,
        "start_time": event.start_time.isoformat(),
        "end_time": event.end_time.isoformat(),
    }), 201


@team_bp.route("/<team_id>/events", methods=["GET"])
def list_team_events_route(team_id):
    events = TeamEvent.objects(team_id=team_id).order_by("-start_time")
    return jsonify([
        {
            "id": str(e.id),
            "team_id": e.team_id,
            "title": e.title,
            "start_time": e.start_time.isoformat(),
            "end_time": e.end_time.isoformat(),
            "location": e.location,
        }
        for e in events
    ]), 200


@team_bp.route("/<team_id>/members/<member_id>", methods=["DELETE"])
def remove_member_route(team_id, member_id):
    data = request.get_json() or {}
    owner_id = data.get("owner_id") or request.args.get("owner_id")

    if not owner_id:
        return jsonify({"error": "owner_id is required"}), 400

    ok, error = remove_member(team_id=team_id, owner_id=owner_id, member_id=member_id)
    if error:
        return jsonify({"error": error}), 403

    return jsonify({"message": "Member removed"}), 200


@team_bp.route("/<team_id>", methods=["DELETE"])
def delete_team_route(team_id):
    data = request.get_json() or {}
    owner_id = data.get("owner_id") or request.args.get("owner_id")

    if not owner_id:
        return jsonify({"error": "owner_id is required"}), 400

    ok, error = delete_team(team_id=team_id, owner_id=owner_id)
    if error:
        return jsonify({"error": error}), 403

    return jsonify({"message": "Team deleted"}), 200
