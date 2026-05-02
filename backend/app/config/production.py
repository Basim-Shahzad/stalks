from .base import BaseConfig

class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    # Add prod-only vars here