import os


class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def from_env(cls):
        cls.SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
        cls.CORS_ORIGINS = os.environ["CORS_ORIGINS"].split(",")
        return cls
