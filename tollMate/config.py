"""Flask configuration."""
from os import environ, path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class ConfigurationError(Exception):
    """Raised when a configuration parameter is invalid or undefined"""
    pass


class Config:
    """Base config."""
    SECRET_KEY = environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = environ.get('SESSION_COOKIE_NAME')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
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

