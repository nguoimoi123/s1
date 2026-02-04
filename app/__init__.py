from flask import Flask
from .config import Config
from .extensions import db, socketio
from .auth.google import auth_bp
from .routes.summarize_routes import bp
from .routes.user_router import user_bp
from .routes.folder_router import folder_bp
from .routes.file_router import file_bp
from .routes.chunk_router import chunk_bp
from .routes.chat_notebook_router import chat_bp
from .routes.meeting_routes import meeting_bp
from .routes.chat_routes import bp as chatm_bp
from .routes.reminder_routes import reminder_bp
from .routes.report_routes import report_bp
from .routes.search_routes import search_bp
from .routes.team_routes import team_bp
from .models.team_model import Team
from .models.team_member_model import TeamMember
from .models.team_event_model import TeamEvent
from .models.team_invite_model import TeamInvite
from .models.meeting_model import Meeting
from .models.folder_model import Folder
from .models.file_model import File
from .services.plan_service import ensure_default_upgrade_codes
import app.sockets.meeting_socket
import app.sockets.notification_socket


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    app.register_blueprint(bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(folder_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(chunk_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(meeting_bp)
    app.register_blueprint(chatm_bp)
    app.register_blueprint(reminder_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(team_bp)

    # Seed default upgrade codes (admin will distribute these)
    try:
        ensure_default_upgrade_codes(plus_count=10, premium_count=10)
    except Exception as e:
        print(f"Failed to seed upgrade codes: {e}")

    # Ensure indexes for search
    try:
        Meeting.ensure_indexes()
        Folder.ensure_indexes()
        File.ensure_indexes()
        Team.ensure_indexes()
        TeamMember.ensure_indexes()
        TeamEvent.ensure_indexes()
        TeamInvite.ensure_indexes()
    except Exception as e:
        print(f"Failed to ensure indexes: {e}")

    return app
