#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import argparse
from os import environ
from datetime import datetime
import json

from hacGpsPoints import HAC_gpsPoints, HAC_gpsPoints_Error

from tollMate import db, models

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# check if debugging requested via environment variable DEBUG
try:
    DEBUG = int(environ.get('DEBUG'))
except:
    DEBUG = 0


def parse_args(args):
    """ Parse cmdline args """
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--log-file", help="log file name to be created",
                        default="test-db-{:%Y%m%d}.log")
    parser.add_argument("args", nargs='*')
    return parser.parse_args(args)


def logging_init(args):
    """ Initialize logging """
    global DEBUG
    logging.basicConfig(filename=args.log_file.format(datetime.now()),
        level = logging.DEBUG if DEBUG else logging.INFO,
        format = '%(asctime)s %(levelname)s %(message)s')


def main():
    args = parse_args(sys.argv[1:])
    logging_init(args)
    logging.info("testing started, with DEBUG environment variable value set to {}".format(repr(DEBUG)))
    models.routetab_get_by_id(2)
    logging.info("testing finished")
    return 0

if __name__ == "__main__":
    sys.exit(main())
