from flask import Blueprint, request, jsonify
from ..services.user_service import UserController
from ..services.plan_service import get_plan_limits, get_user_plan, create_upgrade_codes, redeem_upgrade_code
from ..services.usage_service import get_usage

user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route("/add", methods=["POST"])
def add_user():
    data = request.get_json()
    print(data)
    if not data:
        return {"error": "No data provided"}, 400
    response, status = UserController.create_user(
        name=data["name"],
        email=data["email"],
        password=data["password"]
    )
    return jsonify(response), status

#[POST] http://127.0.0.1:5000/user/<user_id>
@user_bp.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    response, status = UserController.get_user(user_id)
    return jsonify(response), status


@user_bp.route("/login", methods=["POST"])
def login_user():
    data = request.get_json()
    if not data:
        return {"error": "No data provided"}, 400
    if not data.get("email") or not data.get("password"):
        return {"error": "Email and password are required"}, 400

    response, status = UserController.login(
        email=data["email"],
        password=data["password"],
    )
    return jsonify(response), status


@user_bp.route("/plan/<user_id>", methods=["GET"])
def get_user_plan_info(user_id):
    plan = get_user_plan(user_id)
    limits = get_plan_limits(plan)
    return jsonify({"plan": plan, "limits": limits}), 200


@user_bp.route("/upgrade-code/create", methods=["POST"])
def create_upgrade_code():
    data = request.get_json() or {}
    plan = data.get("plan")
    count = int(data.get("count", 1))

    if plan not in ("plus", "premium"):
        return {"error": "Invalid plan"}, 400

    codes = create_upgrade_codes(plan, count)
    return jsonify({
        "plan": plan,
        "codes": [c.code for c in codes],
    }), 201


@user_bp.route("/upgrade", methods=["POST"])
def upgrade_plan():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    code_value = data.get("code")

    if not user_id or not code_value:
        return {"error": "user_id and code are required"}, 400

    user, error = redeem_upgrade_code(user_id, code_value)
    if error:
        return {"error": error}, 400

    return jsonify({
        "message": "Plan upgraded",
        "plan": user.plan,
        "user_id": str(user.id),
    }), 200


@user_bp.route("/usage/<user_id>", methods=["GET"])
def get_user_usage(user_id):
    data, error = get_usage(user_id)
    if error:
        return {"error": error}, 404
    return jsonify(data), 200
