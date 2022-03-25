# main Flask application init file

from os import environ
import logging
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask.logging import default_handler
from flask_log_request_id import RequestID, RequestIDLogFilter, current_request_id

from . import log, config


def logging_init():
    """ Initialize logging """
    DEBUG = environ.get('DEBUG', None)

    logname = "FLASK-APP.log"
    # This is the one that we need to write it to our log file
    handler = logging.FileHandler(logname)
    # Setup logging
    # handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - level=%(levelname)s - request_id=%(request_id)s - %(message)s"))
    # << Add request id contextual filter
    handler.addFilter(RequestIDLogFilter())
    # adding handler to ROOT logger
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    # handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(request_id)s - %(message)s")) # i make the format more compact

    # fixing 'werkzeug' logger
    handler = logging.handlers.RotatingFileHandler(
        'werkzzz.log', maxBytes=8 * 1024 * 1024)
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)
    logging.getLogger('werkzeug').addHandler(handler)
    # app.logger.setLevel(logging.WARNING)
    # app.logger.addHandler(handler)


def init_app():
    app = Flask(__name__)
    app.config.from_object(config.DevConfig)
    app.config["LOG_TYPE"] = environ.get("LOG_TYPE", "stream")
    app.config["LOG_LEVEL"] = environ.get("LOG_LEVEL", "INFO")

    RequestID(app)
    app.logger.removeHandler(default_handler)
    logging_init()

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
