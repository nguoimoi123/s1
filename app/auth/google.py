from flask import Blueprint, request, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from ..models.user_model import User
from mongoengine.errors import NotUniqueError

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth/google", methods=["POST"])
def google_login():
    data = request.get_json()
    if not data or "id_token" not in data:
        return jsonify({"error": "id_token is required"}), 400

    token = data["id_token"]

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID")
        )

        email = idinfo["email"]
        name = idinfo.get("name")
        avatar = idinfo.get("picture")

        user = User.objects(email=email).first()
        if not user:
            user = User(email=email, name=name, avatar=avatar, plan="free")
            user.save()
        else:
            user.update(name=name, avatar=avatar)

        return jsonify({
            "message": "Login success",
            "user_id": str(user.id),
            "email": email,
            "name": name,
            "avatar": avatar,
            "plan": user.plan
        }), 200

    except NotUniqueError:
        return jsonify({"error": "Email already exists"}), 409
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
