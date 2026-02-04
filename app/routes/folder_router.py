from flask import Blueprint, request, jsonify
from app.services.folder_service import FolderController

folder_bp = Blueprint("folder", __name__, url_prefix="/folder")


@folder_bp.route("/add", methods=["POST"])
def add_folder():
    data = request.get_json()
    if not data:
        return {"error": "No data provided"}, 400
    response, status = FolderController.create_folder(
        user_id=data["user_id"],
        name=data["name"],
        description=data["description"],
    )
    return jsonify(response), status

@folder_bp.route("/<user_id>", methods=["GET"])
def get_folders(user_id):
    response, status = FolderController.get_folders_by_user(user_id)
    return jsonify(response), status
@folder_bp.route("/delete/<folder_id>", methods=["DELETE"])
def delete_folder(folder_id):
    response, status = FolderController.delete_folder(folder_id)
    return jsonify(response), status