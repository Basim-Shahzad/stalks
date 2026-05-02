from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
    # Add dev-only vars here
