import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import configs

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    env = os.environ.get('FLASK_ENV', 'development')
    print("Enviroment:", env.upper())
    load_dotenv(f'.env.{env}')

    config = configs[env]
    config.from_env()

    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app, origins=app.config["CORS_ORIGINS"])

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)

    from .models import Transaction

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app