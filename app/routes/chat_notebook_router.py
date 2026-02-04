from flask import Blueprint, request, jsonify
from app.services.chat_notebook_service import ChatNotebookController

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")

@chat_bp.route("/notebook", methods=["POST"])
def chat_notebook():
    data = request.json

    response, status = ChatNotebookController.chat_bot_notebook(
        user_id=data.get("user_id"),
        folder_id=data.get("folder_id"),
        question=data.get("question"),
        file_ids=data.get("file_ids"),
        top_k=data.get("top_k", 5)
    )

    return jsonify(response), status