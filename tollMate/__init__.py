# main Flask application init file

from os import environ
import logging
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask.logging import default_handler

from . import log, config

def logging_init():
    """ Initialize logging """
    DEBUG = environ.get('DEBUG', None)
    logging.basicConfig(filename="FLASK-APP.log",
        level = logging.DEBUG if DEBUG else logging.INFO,
        format = '%(asctime)s %(levelname)s %(message)s')

def init_app():
    app = Flask(__name__)
    app.config.from_object(config.DevConfig)
    app.config["LOG_TYPE"] = environ.get("LOG_TYPE", "stream")
    app.config["LOG_LEVEL"] = environ.get("LOG_LEVEL", "INFO")    
    app.logger.removeHandler(default_handler)
    logger = logging.getLogger(__name__)
    # logging_init()
    db = SQLAlchemy(app)
    return (app, db)

(app,db) = init_app()

@app.teardown_appcontext
def shutdown_session(exception=None):
    # this does also app.db.close()
    db.session.remove()

from . import models, views
