import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    REDIS_KEY = os.getenv('REDIS_KEY')
    REDIS_URL = os.getenv('REDIS_URL')
    APP_ID = os.getenv('APP_ID')
    KEY_PUSHER = os.getenv('KEY_PUSHER')
    SECRET_PUSHER = os.getenv('SECRET_PUSHER')
    API_KEY = os.getenv('API_KEY')
    KEY_REDIS = os.getenv('KEY_REDIS')
    REDIS_URL = os.getenv('REDIS_URL')

    UPLOAD_FOLDER = "./videos"

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI')
    
config_by_name = dict(
    development=DevelopmentConfig
)