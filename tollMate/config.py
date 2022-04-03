"""Flask configuration."""
from os import environ, path, urandom
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class ConfigurationError(Exception):
    """Raised when a configuration parameter is invalid or undefined"""
    pass


class Config:
    """Base config."""
    SECRET_KEY = environ.get('SECRET_KEY', None)
    if not SECRET_KEY:
        SECRET_KEY = urandom(24)
        raise ValueError("No SECRET_KEY set for Flask application")

    SESSION_COOKIE_NAME = environ.get('SESSION_COOKIE_NAME')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
    DATASTORE_FOLDER = 'datastore'
    UPLOAD_EXTENSIONS = [ 'xlsx', 'xls' ]
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024
    LOG_REQUEST_ID_GENERATE_IF_NOT_FOUND = True
    LOG_REQUEST_ID_LOG_ALL_REQUESTS = True
    JSON_SORT_KEYS = False
    def SQLALCHEMY_DATABASE_URI():
        raise ConfigurationError("SQLALCHEMY_DATABASE_URI has to be overriden in per-deployment config")


class ProdConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = environ.get('PROD_DATABASE_URI')


class DevConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = environ.get('DEV_DATABASE_URI')

