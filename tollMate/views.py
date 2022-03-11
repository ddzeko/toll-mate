# views.py

import logging
from flask import abort, json
from . import app, db

@app.route('/')
def hello_world():
    try:
        return f'Hello from tollMate-view!'
    except Exception as e:
            logging.error (e.__class__.__name__)
            db.session.rollback ()
            abort (500, 'Error. Something bad happened.')