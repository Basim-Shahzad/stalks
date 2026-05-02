from flask import Blueprint, jsonify, request
from .services.transactions_service import process_file
from .services.psx_service import psx
from pathlib import Path
import os
import tempfile
import uuid
import json
from .models import Transaction

main_bp = Blueprint("main", __name__)

TRANSACTIONS_OUTPUT_FILE = os.environ.get(
    "TRANSACTIONS_OUTPUT_FILE", "transactions_v1.json"
)


@main_bp.route("/stocks")
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
def clear_cache():
    """
    DELETE /stocks/cache          — clears all
    DELETE /stocks/cache?symbol=OGDC — clears one
    """
    symbol = request.args.get("symbol")
    psx.invalidate_cache(symbol.upper() if symbol else None)
    return jsonify({"invalidated": symbol.upper() if symbol else "all"})


@main_bp.route("/transactions", methods=["POST", "GET"])
def get_create_transactions():

    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No File"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "Empty filename"}), 400
        tmp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.pdf")
        try:
            file.save(tmp_path)
            result = process_file(tmp_path)
            if result["success"]:
                return jsonify(result), 200
            else:
                return jsonify(result), 500  # not confirm status code
        finally:
            os.remove(tmp_path)

    elif request.method == "GET":
        try:
            results = Transaction.query.all()
            return (
                jsonify({"success": True, "data": [t.to_dict() for t in results]}),
                200,
            )
        except FileNotFoundError:
            return jsonify({"success": False, "error": "Server Error"}), 500