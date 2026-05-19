import logging

logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)

logger.propagate = False

formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

file_handler = logging.FileHandler("app.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
