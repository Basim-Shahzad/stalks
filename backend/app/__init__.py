import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from .config import configs

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app():
    env = os.environ.get("FLASK_ENV", "development")
    print("Enviroment:", env.upper())
    load_dotenv(f".env.{env}")

    config = configs[env]
    config.from_env()

    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app, origins=app.config["CORS_ORIGINS"])

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    jwt.init_app(app)

    from .models import Transaction, TokenBlocklist, User, Portfolio

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        return db.session.query(
            TokenBlocklist.query.filter_by(jti=jti).exists()
        ).scalar()

    @jwt.revoked_token_loader
    def revoked_token_response(jwt_header, jwt_payload):
        return {"success": False, "error": "Token has been revoked"}, 401

    @jwt.expired_token_loader
    def expired_token_response(jwt_header, jwt_payload):
        return {"success": False, "error": "Token has expired"}, 401

    @jwt.invalid_token_loader
    def invalid_token_response(reason):
        return {"success": False, "error": f"Invalid token: {reason}"}, 422

    @jwt.unauthorized_loader
    def missing_token_response(reason):
        return {"success": False, "error": "Authorization token required"}, 401

    from .routes import main_bp

    app.register_blueprint(main_bp)

    return app
