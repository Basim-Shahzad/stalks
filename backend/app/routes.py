from flask import Blueprint, jsonify, request
from .services.stock_service import get_bulk_stock_data, get_single_stock_detail
from .services.stocks_data_services import get_stocks_data

main_bp = Blueprint('main', __name__)

ALL_SYMBOLS = [
    "AHCL.KA", "AICL.KA", "AKBL.KA", "ATLH.KA", "ATRL.KA", "BAFL.KA",
    "BIPL.KA", "BOP.KA", "CNERGY.KA", "DGKC.KA", "EFERT.KA", "ENGRO.KA",
    "FFC.KA", "FFL.KA", "GHNI.KA", "GLAXO.KA", "ILP.KA", "JDWS.KA",
    "JVDC.KA", "KEL.KA", "LUCK.KA", "MCB.KA", "MEBL.KA", "MFFL.KA",
    "MLCF.KA", "MTL.KA", "NATF.KA", "NCPL.KA", "NML.KA", "NPL.KA",
    "OCTOPUS.KA", "OGDC.KA", "PAKQATAR.KA", "PAKT.KA", "PKGS.KA",
    "POWER.KA", "PPL.KA", "PRL.KA", "PSO.KA", "PSX.KA", "SAZEW.KA",
    "SEARL.KA", "SML.KA", "SNGP.KA", "SRVI.KA", "SYS.KA", "TPL.KA", "UBL.KA"
]

@main_bp.route("/")
def index():
    return "Hey"

@main_bp.route("/stocks")
def get_stocks():
    data = get_stocks_data()
    return jsonify(data)

# @main_bp.route("/stocks")
# def stock_data():
#     page = request.args.get('page', 1, type=int)
#     # Pagination: fetches 10 at a time
#     data = get_bulk_stock_data(ALL_SYMBOLS, page=page, per_page=10)
#     return jsonify(data)

# @main_bp.route("/stocks/<symbol>")
# def single_stock(symbol):
#     data = get_single_stock_detail(symbol)
#     status_code = 404 if "error" in data else 200
#     return jsonify(data), status_code