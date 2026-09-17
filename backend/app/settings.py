from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Hermes OS"
    app_env: str = "development"
    hermes_profile: str = "restaurant"
    hermes_modules: str = ""


settings = Settings()
