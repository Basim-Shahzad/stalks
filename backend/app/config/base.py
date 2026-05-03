import os


class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def from_env(cls):
        raw_uri = os.environ["SQLALCHEMY_DATABASE_URI"]
        
        if raw_uri.startswith("sqlite:///./"):
            rel_path = raw_uri.replace("sqlite:///./", "")
            abs_path = os.path.join(os.getcwd(), rel_path)
            cls.SQLALCHEMY_DATABASE_URI = f"sqlite:///{abs_path}"
        else:
            cls.SQLALCHEMY_DATABASE_URI = raw_uri
        
        cls.CORS_ORIGINS = os.environ["CORS_ORIGINS"].split(",")

        cls.JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
        cls.JWT_ACCESS_TOKEN_EXPIRES = 900
        cls.JWT_REFRESH_TOKEN_EXPIRES = 2592000
        cls.JWT_TOKEN_LOCATION = ["headers", "cookies"]