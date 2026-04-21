import os

class Config:
    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "fallback_secret_key")

settings = Config()
