from .development import DevelopmentConfig
from .production import ProductionConfig

configs = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
