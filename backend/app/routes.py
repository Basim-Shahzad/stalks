from flask import Blueprint, jsonify, request
from .services.stocks_data_services import get_stocks_data
from .services.transactions_services import process_file
from pathlib import Path
import os
import tempfile
import uuid
import json

main_bp = Blueprint("main", __name__)

TRANSACTIONS_OUTPUT_FILE = os.environ.get('TRANSACTIONS_OUTPUT_FILE', 'transactions_v1.json')

@main_bp.route("/")
def index():
    return "Hey"


@main_bp.route("/stocks")
def get_stocks():
    data = get_stocks_data()
    return jsonify(data)


@main_bp.route("/transactions", methods=["POST", "GET"])
def get_create_transactions():

    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"success": False, "error": "No File"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "Empty filename"}), 400
        tmp_path = os.path.join(
            tempfile.gettempdir(),
            f"{uuid.uuid4()}.pdf"
        )
        try:
            file.save(tmp_path)
            result = process_file(tmp_path)
            if result["success"]:
                return jsonify(result), 200 # TODO: ADD A DB CALL TO FETCH ALL TRANSACTIONS AND GIVE IT
            else:
                return jsonify(result), 500 # not confirm status code
        finally:
            os.remove(tmp_path)

    elif request.method == "GET":
        current_dir = Path(__file__).parent
        file_path = current_dir / "data" / TRANSACTIONS_OUTPUT_FILE
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
            return jsonify({"success": True, "data": data})
        except FileNotFoundError:
            return jsonify({"success": False, "error": "File not found"})
