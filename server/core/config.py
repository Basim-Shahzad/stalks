from pathlib import Path
import tomllib
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
PROJECT_VERSION = tomllib.loads(
    (BASE_DIR / "pyproject.toml").read_text(encoding="utf-8")
)["project"]["version"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding="utf-8")

    SQLALCHEMY_DATABASE_URI: str

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    app_env: str

    stalks_data_api_base_url: str
    stalks_data_api_key: SecretStr


settings = Settings()