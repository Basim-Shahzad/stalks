from flask import Blueprint, jsonify, request
from .services.psx_service import psx
import os
import tempfile
import uuid
from .models import Transaction, User, Portfolio, TokenBlocklist
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_jwt,
)
from helpers.auth_helpers import (
    hash_password,
    verify_password,
    validate_password,
    validate_email,
    _blocklist_jti,
)
from helpers.files_helpers import secure_it, get_extension, is_allowed
from helpers.transactions_helper import parse_transactions_csv, parse_transactions_pdf
from app import db

main_bp = Blueprint("main", __name__)

TRANSACTIONS_OUTPUT_FILE = os.environ.get(
    "TRANSACTIONS_OUTPUT_FILE", "transactions_v1.json"
)


@main_bp.route("/stocks")
@jwt_required()
def get_stocks():
    """
    GET /stocks?page=1&page_size=10          — paginated (default)
    GET /stocks?paginated=false              — all stocks, no pagination

    Paginated response:
    {
        "page": 1,
        "page_size": 10,
        "total": 51,
        "total_pages": 6,
        "has_next": true,
        "has_prev": false,
        "stocks": [ { "symbol": "OGDC", "data": {...}, "fetched_at": "..." }, ... ]
    }

    Unpaginated response:
    {
        "total": 51,
        "stocks": [ { "symbol": "OGDC", "data": {...}, "fetched_at": "..." }, ... ]
    }
    """
    paginated = request.args.get("paginated", "true").lower() != "false"

    if not paginated:
        try:
            data = psx.get_all()
        except Exception as exc:
            return jsonify({"error": "upstream fetch failed", "detail": str(exc)}), 502
        return jsonify(data)

    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", psx.page_size))
    except ValueError:
        return jsonify({"error": "page and page_size must be integers"}), 400

    # Allow per-request page_size override
    psx.page_size = page_size

    try:
        data = psx.get_page(page)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": "upstream fetch failed", "detail": str(exc)}), 502

    return jsonify(data)


@main_bp.route("/stocks/<symbol>")
@jwt_required()
def get_stock(symbol: str):
    """
    GET /stocks/OGDC
    """
    try:
        data = psx.get_symbol(symbol)
    except Exception as exc:
        return (
            jsonify({"error": f"could not fetch {symbol.upper()}", "detail": str(exc)}),
            502,
        )

    return jsonify(data)


@main_bp.route("/stocks/cache", methods=["DELETE"])
@jwt_required()
def clear_cache():
    """
    DELETE /stocks/cache          — clears all
    DELETE /stocks/cache?symbol=OGDC — clears one
    """
    symbol = request.args.get("symbol")
    psx.invalidate_cache(symbol.upper() if symbol else None)
    return jsonify({"invalidated": symbol.upper() if symbol else "all"})


@main_bp.route("/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
    try:
        user_id = get_jwt_identity()
        portfolio_id: uuid.UUID = request.args.get("portfolio_id")

        if not portfolio_id:
            return jsonify({"error": "portfolio_id is required"}), 400

        portfolio = Portfolio.query.filter_by(
            user_id=str(user_id), id=str(portfolio_id)
        ).first()

        if not portfolio:
            return jsonify({"success": False, "error": "Portfolio not found"}), 404

        return (
            jsonify(
                {"success": True, "data": [t.to_dict() for t in portfolio.transactions]}
            ),
            200,
        )

    except Exception:
        return jsonify({"success": False, "error": "Server Error"}), 500


@main_bp.route("/transactions", methods=["POST"])
@jwt_required()
def create_transactions():
    json_data = request.get_json(silent=True)
    portfolio_id: uuid.UUID = request.args.get("portfolio_id")

    if not portfolio_id:
        return jsonify({"success": False, "error": "portfolio_id is required"}), 400

    if json_data:
        transaction = Transaction(portfolio_id=portfolio_id, **json_data)
        db.session.add(transaction)
        db.session.commit()
        return jsonify({"success": True, "data": transaction.to_dict()}), 201

    if "file" in request.files:
        file = request.files["file"]

        if file.filename == "" or not is_allowed(file.filename):
            return jsonify({"success": False, "error": "Only CSV and PDF allowed"}), 400

        ext = get_extension(file.filename)
        safe_name = secure_it(file.filename)

        if not safe_name:
            return jsonify({"success": False, "error": "Invalid file name"}), 400

        parser = parse_transactions_pdf if ext == "pdf" else parse_transactions_csv

        tmp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.{ext}")
        try:
            file.save(tmp_path)
            result = parser(tmp_path, portfolio_id=portfolio_id)
            status_code = 200 if result.get("success") else 400
            return jsonify(result), status_code
        except Exception as e:
            return (
                jsonify({"success": False, "error": f"Processing failed: {str(e)}"}),
                500,
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return (
        jsonify({"success": False, "error": "No transaction data or file provided"}),
        400,
    )


# AUTH ROUTES


@main_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "No JSON body"}), 400

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")
    username = data.get("username", "").strip()

    if not (email and password and username):
        return jsonify({"success": False, "error": "Missing required fields"}), 400
    if not validate_email(email):
        return jsonify({"success": False, "error": "Invalid email address"}), 422
    if not validate_password(password):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Password must be ≥8 chars and include uppercase, lowercase, digit, and symbol",
                }
            ),
            422,
        )
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "Email already registered"}), 409

    user = User(email=email, password=hash_password(password), username=username)
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "user": user.to_dict(),
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
            }
        ),
        201,
    )


@main_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"success": False, "error": "No JSON body"}), 400

    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    if not (email and password):
        return jsonify({"success": False, "error": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not verify_password(password, user.password):
        return jsonify({"success": False, "error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
            }
        ),
        200,
    )


@main_bp.route("/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    refresh_token = create_refresh_token(identity=user_id)

    # Blocklist the old refresh token immediately (rotation)
    jti = get_jwt()["jti"]
    _blocklist_jti(jti)

    return (
        jsonify(
            {
                "success": True,
                "data": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                },
            }
        ),
        200,
    )


@main_bp.route("/auth/logout", methods=["DELETE"])
@jwt_required(verify_type=False)  # accepts access OR refresh token
def logout():
    jti = get_jwt()["jti"]
    token_type = get_jwt().get("type", "access")
    _blocklist_jti(jti)

    return (
        jsonify(
            {
                "success": True,
                "message": f"{token_type.capitalize()} token revoked. Goodbye.",
            }
        ),
        200,
    )


@main_bp.route("/auth/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    return jsonify({"success": True, "data": user.to_dict()}), 200


# Portfolio routes


@main_bp.route("/portfolios", methods=["GET", "POST"])
@jwt_required()
def get_create_portfolios():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    if request.method == "POST":
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "No JSON body"}), 400

        name = data.get("name", "").strip()
        description = data.get("description", "").strip()

        if not (name and description):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        portfolio = Portfolio(user_id=user_id, name=name, description=description)
        db.session.add(portfolio)
        db.session.commit()

        return jsonify({"success": True, "data": portfolio.to_dict()}), 201

    if request.method == "GET":
        return (
            jsonify({"success": True, "data": [p.to_dict() for p in user.portfolios]}),
            200,
        )


@main_bp.route("/portfolios/<uuid:portfolio_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def get_update_delete_portfolio(portfolio_id: uuid.UUID):
    user_id = get_jwt_identity()
    portfolio = Portfolio.query.filter_by(user_id=user_id, id=portfolio_id).first()

    if not portfolio:
        return jsonify({"success": False, "error": "Portfolio not found"}), 404

    if request.method == "GET":
        return jsonify({"success": True, "data": portfolio.to_dict()}), 200

    if request.method == "PUT":
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "No JSON body"}), 400

        name = data.get("name", "").strip()
        description = data.get("description", "").strip()

        if not (name and description):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        portfolio.name = name
        portfolio.description = description
        db.session.commit()

        return jsonify({"success": True, "data": portfolio.to_dict()}), 200
