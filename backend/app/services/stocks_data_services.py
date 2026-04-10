import requests

# 49 unique as of now
unique_stocks = [
    "AHCL",
    "AICL",
    "AKBL",
    "ANL",
    "ATLH",
    "ATRL",
    "BAFL",
    "BIPL",
    "BOP",
    "CNERGY",
    "DGKC",
    "EFERT",
    "ENGROH",
    "FFC",
    "FFL",
    "GHNI",
    "GLAXO",
    "ILP",
    "JDWS",
    "JVDC",
    "KEL",
    "LUCK",
    "MCB",
    "MEBL",
    "MFFL",
    "MLCF",
    "MTL",
    "NATF",
    "NCPL",
    "NML",
    "NPL",
    "OCTOPUS",
    "OGDC",
    "PAKQATAR",
    "PAKT",
    "PKGS",
    "POWER",
    "PPL",
    "PRL",
    "PSO",
    "PSX",
    "SAZEW",
    "SEARL",
    "SML",
    "SNGP",
    "SRVI",
    "SYS",
    "TPL",
    "UBL",
]

def get_stocks_data():
    stocks = unique_stocks[:10]
    stocks_data = []
    for stock in stocks:
        res = requests.get(f"https://psxterminal.com/api/ticks/REG/{stock}")
        stocks_data.append(res.json()["data"])

    if res.status_code == 200:
        return stocks_data
    else:
        return res.json()