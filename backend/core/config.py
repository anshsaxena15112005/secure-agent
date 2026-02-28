from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    app_name: str = "Secure Agent"
    environment: str = "development"
    debug: bool = True

settings = AppSettings()
