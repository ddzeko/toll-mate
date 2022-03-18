#!/bin/bash
DEBUG=True
FLASK_ENV=development
export DEBUG FLASK_ENV
python ./wsgi.py
