from flask import Blueprint

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return "Welcome!"


@main_bp.route("/hello/<username>")
def show_user(username):
    return f"Hello, {username}!"
