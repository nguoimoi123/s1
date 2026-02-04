from flask import Blueprint, request, jsonify, send_file
from app.services.file_service import FileController

file_bp = Blueprint("file", __name__, url_prefix="/file")

@file_bp.route("/upload", methods=["POST"])
def upload_file():
    data = request.get_json()
    if not data:
        return {"error": "No data provided"}, 400
    response, status = FileController.upload_file(
        user_id=data.get("user_id"),
        folder_id=data.get("folder_id"),
        filename=data.get("filename"),
        file_type=data.get("file_type"),
        size=data.get("size"),
        content=data.get("content")
    )
    return jsonify(response), status

@file_bp.route("/folder/<folder_id>", methods=["GET"])
def get_files_by_folder(folder_id):
    response, status = FileController.get_files_by_folder(folder_id)
    return jsonify(response), status


@file_bp.route("/delete/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    response, status = FileController.delete_file(file_id)
    return jsonify(response), status


@file_bp.route("/download/<file_id>", methods=["GET"])
def download_file(file_id):
    buffer, filename, mimetype, error, status = FileController.get_file_for_download(file_id)
    if status != 200:
        return jsonify(error), status

    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype,
    )