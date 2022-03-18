#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tollMate import db, models

if __name__ == '__main__':
    db.drop_all()
    db.create_all()
    #
    upload1 = models.Uploads(orig_filename="One.xls", dest_filename="421414.xls")
    db.session.add(upload1)
    #
    db.session.commit()
    #
    db.session.remove()
    print('Done.')
