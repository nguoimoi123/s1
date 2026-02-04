from datetime import datetime
from typing import List
import os
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models.team_model import Team
from app.models.team_member_model import TeamMember
from app.models.team_event_model import TeamEvent
from app.models.team_invite_model import TeamInvite
from app.models.user_model import User
from app.services.reminder_service import ReminderController
from app.extensions import socketio


def _get_user(user_id: str):
    return User.objects(id=user_id).first()


def _get_or_create_user_by_email(email: str):
    user = User.objects(email=email).first()
    if user:
        return user, False

    name = email.split("@")[0] if "@" in email else email
    user = User(email=email, name=name, plan="free")
    user.save()
    return user, True


def _send_invite_email(email: str, team_name: str, invite_link: str):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "0") or 0)
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SMTP_FROM") or username

    if not host or not port or not sender:
        return False, "SMTP not configured"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"You've been invited to {team_name}"
    msg["From"] = sender
    msg["To"] = email

    text = f"Chào mừng mày đến với {team_name}. Open: {invite_link}"
    msg.attach(MIMEText(text, "plain"))

    with smtplib.SMTP(host, port) as server:
        if os.getenv("SMTP_TLS", "true").lower() == "true":
            server.starttls()
        if username and password:
            server.login(username, password)
        server.sendmail(sender, [email], msg.as_string())

    return True, None


def _require_plan(user_id: str, allowed: List[str]):
    user = _get_user(user_id)
    if not user:
        return None, "User not found"
    if user.plan not in allowed:
        return None, f"Plan '{user.plan}' not allowed"
    return user, None


def create_team(owner_id: str, name: str):
    user, error = _require_plan(owner_id, ["premium"])
    if error:
        return None, error

    team = Team(name=name, owner_id=owner_id)
    team.save()

    TeamMember(
        team_id=str(team.id),
        user_id=owner_id,
        role="owner",
        status="active",
    ).save()

    return team, None


def list_user_teams(user_id: str):
    memberships = TeamMember.objects(user_id=user_id, status="active")
    team_ids = [m.team_id for m in memberships]
    teams = Team.objects(id__in=team_ids)
    return teams


def list_team_members(team_id: str):
    return TeamMember.objects(team_id=team_id)


def invite_member(team_id: str, owner_id: str, member_id: str = None, member_email: str = None):
    owner = TeamMember.objects(team_id=team_id, user_id=owner_id, role="owner").first()
    if not owner:
        return None, "Only team owner can invite"

    if member_id is None and member_email is None:
        return None, "member_id or member_email required"

    team = Team.objects(id=team_id).first()
    team_name = team.name if team else "Team"

    if member_id is None:
        user, _ = _get_or_create_user_by_email(member_email)
        member_id = str(user.id)

    existing = TeamMember.objects(team_id=team_id, user_id=member_id).first()
    if existing:
        return existing, None

    member = TeamMember.objects(team_id=team_id, user_id=member_id).first()
    if not member:
        member = TeamMember(team_id=team_id, user_id=member_id, role="member", status="invited")
        member.save()

    if member_email:
        token = secrets.token_urlsafe(24)
        TeamInvite(
            team_id=team_id,
            email=member_email,
            token=token,
            invited_by=owner_id,
        ).save()

        base_url = os.getenv("APP_INVITE_BASE_URL", "")
        invite_link = f"{base_url}?token={token}" if base_url else token
        try:
            _send_invite_email(member_email, team_name, invite_link)
        except Exception:
            pass

    try:
        socketio.emit(
            "team_invite",
            {
                "team_id": team_id,
                "team_name": team_name,
                "invited_by": owner_id,
            },
            room=member_id,
        )
    except Exception:
        pass

    return member, None


def accept_invite(team_id: str, user_id: str):
    user = _get_user(user_id)
    if not user:
        return None, "User not found"

    plan_changed = False
    if user.plan == "free":
        user.plan = "plus"
        user.save()
        plan_changed = True

    _, error = _require_plan(user_id, ["plus", "premium"])
    if error:
        return None, error, plan_changed, user.plan

    member = TeamMember.objects(team_id=team_id, user_id=user_id).first()
    if not member:
        return None, "Invite not found"

    member.status = "active"
    member.joined_at = datetime.utcnow()
    member.save()
    return member, None, plan_changed, user.plan


def accept_invite_by_token(token: str, user_id: str = None, email: str = None):
    invite = TeamInvite.objects(token=token, status="invited").first()
    if not invite:
        return None, "Invite not found"
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        invite.status = "expired"
        invite.save()
        return None, "Invite expired"

    user = None
    if user_id:
        user = _get_user(user_id)
    if not user and email:
        user, _ = _get_or_create_user_by_email(email)

    if not user:
        return None, "User not found"

    member = TeamMember.objects(team_id=invite.team_id, user_id=str(user.id)).first()
    if not member:
        member = TeamMember(team_id=invite.team_id, user_id=str(user.id), role="member", status="invited")
        member.save()

    member, error, plan_changed, plan = accept_invite(invite.team_id, str(user.id))
    if error:
        return None, error

    invite.status = "accepted"
    invite.save()

    return {
        "team_id": invite.team_id,
        "user_id": str(user.id),
        "plan_changed": plan_changed,
        "plan": plan,
    }, None


def remove_member(team_id: str, owner_id: str, member_id: str):
    owner = TeamMember.objects(team_id=team_id, user_id=owner_id, role="owner", status="active").first()
    if not owner:
        return False, "Only team owner can remove members"

    if owner_id == member_id:
        return False, "Owner cannot be removed"

    member = TeamMember.objects(team_id=team_id, user_id=member_id).first()
    if not member:
        return False, "Member not found"

    member.delete()
    return True, None


def delete_team(team_id: str, owner_id: str):
    owner = TeamMember.objects(team_id=team_id, user_id=owner_id, role="owner", status="active").first()
    if not owner:
        return False, "Only team owner can delete team"

    TeamMember.objects(team_id=team_id).delete()
    TeamEvent.objects(team_id=team_id).delete()
    Team.objects(id=team_id).delete()
    return True, None


def list_user_invites(user_id: str):
    invites = TeamMember.objects(user_id=user_id, status="invited")
    team_ids = [m.team_id for m in invites]
    teams = {str(t.id): t for t in Team.objects(id__in=team_ids)}

    result = []
    for invite in invites:
        team = teams.get(invite.team_id)
        result.append({
            "team_id": invite.team_id,
            "team_name": team.name if team else "Team",
            "owner_id": team.owner_id if team else None,
            "status": invite.status,
        })
    return result


def create_team_event(
    team_id: str,
    creator_id: str,
    title: str,
    start_time: datetime,
    end_time: datetime,
    location: str = None,
):
    owner = TeamMember.objects(team_id=team_id, user_id=creator_id, role="owner", status="active").first()
    if not owner:
        return None, "Only team owner can create events"

    _, error = _require_plan(creator_id, ["premium"])
    if error:
        return None, error

    event = TeamEvent(
        team_id=team_id,
        created_by=creator_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        location=location,
    )
    event.save()

    members = TeamMember.objects(team_id=team_id, status="active")
    for member in members:
        ReminderController.create_reminder(
            user_id=member.user_id,
            title=title,
            remind_start=start_time,
            remind_end=end_time,
            location=location,
        )

        try:
            socketio.emit(
                "team_event_created",
                {
                    "team_id": team_id,
                    "title": title,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "location": location,
                },
                room=member.user_id,
            )
        except Exception:
            pass

    return event, None
