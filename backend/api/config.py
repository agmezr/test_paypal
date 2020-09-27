"""Classes used to config the behavior of Flask"""
import dotenv
import os

dotenv.load_dotenv()


class Config:
    DEBUG = True
    TESTING = True
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_TYPE = "filesystem"
    REDIS_URL = os.getenv("REDIS_URL")


class TestConfig(Config):
    DEBUG = True
    TESTING = True


class DevConfig(Config):
    DEBUG = True
    TESTING = False
