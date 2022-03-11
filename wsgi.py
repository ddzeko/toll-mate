#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# to get the env set up, run this via ./run_wsgi.sh

from tollMate import app

if __name__ == "__main__":
    app.run(host='0.0.0.0')
