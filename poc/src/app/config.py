from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Series Scraper Dashboard"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_api_key: str = "YOUR_API_KEY_HERE"

    class Config:
        env_file = ".env"


settings = Settings()
