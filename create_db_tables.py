#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tollMate import db

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    print('Done.')
