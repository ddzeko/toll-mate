# main Flask application init file

from os import environ
import logging
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from . import log, config

def init_app():
    app = Flask(__name__)
    app.config.from_object(config.DevConfig)
    logger = logging.getLogger(__name__)
    db = SQLAlchemy(app)
    return (app, db)

(app,db) = init_app()

@app.teardown_appcontext
def shutdown_session(exception=None):
    # this does also app.db.close()
    db.session.remove()

from . import models, views
