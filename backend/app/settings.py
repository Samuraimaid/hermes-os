from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Hermes OS"
    app_env: str = "development"
    hermes_profile: str = "restaurant"
    hermes_modules: str = ""
    database_url: str = ""
    venue_name: str = "Local demo"
    venue_slug: str = "demo"
    hermes_deployment: str = "local"


settings = Settings()
