from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


settings = Settings()
