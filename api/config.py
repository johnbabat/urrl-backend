import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class ApplicationConfig:

    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    JWT_TOKEN_LOCATION=['cookies']
    JWT_COOKIE_SECURE=eval(os.environ['JWT_COOKIE_SECURE'])
    JWT_COOKIE_SAMESITE=eval(os.environ['JWT_COOKIE_SAMESITE'])
    JWT_COOKIE_CSRF_PROTECT=eval(os.environ['JWT_COOKIE_CSRF_PROTECT'])
    JWT_CSRF_CHECK_FORM=eval(os.environ['JWT_CSRF_CHECK_FORM'])
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=5)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = os.environ["GCP_DATABASE_URL"]
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    FRONTEND=os.environ['FRONTEND']