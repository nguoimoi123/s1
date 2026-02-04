from flask import request
from flask_socketio import join_room
from app.extensions import socketio


@socketio.on("connect")
def on_connect():
    user_id = request.args.get("user_id")
    if user_id:
        join_room(user_id)


@socketio.on("disconnect")
def on_disconnect():
    pass
