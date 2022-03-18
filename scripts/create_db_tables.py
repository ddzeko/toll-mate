#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import path
import sys
SCRIPT_DIR = path.dirname(path.abspath(__file__))
sys.path.append(path.abspath(path.join(SCRIPT_DIR, '..')))

from tollMate import db, models

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    db.session.commit()
    db.session.remove()
    print('Done.')
