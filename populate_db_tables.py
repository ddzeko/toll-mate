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

# check if debugging requested via environment variable DEBUG
try:
    DEBUG = int(environ.get('DEBUG'))
except:
    DEBUG = 0


def load_mjesto_csv():
    csv_row = ("Pirovac", "43.887595092962265,15.787249871525294", "43.88665174671077,15.785769292188363")
    models.mjesto_add(csv_row)
    
    csv_row = ("Kutina", "45.462620831875604,16.76791165361246", "45.46162104834687,16.767158329990483")
    models.mjesto_add(csv_row)


def parse_args(args):
    """ Parse cmdline args """
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--gps-csv-file", help="GPS entry and exit pins file",
                        default="hac-ulazi-izlazi.csv")
    parser.add_argument("-l", "--log-file", help="log file name to be created",
                        default="hac-xform-{:%Y%m%d}.log")
    parser.add_argument("-x", "--output-xlsx", help="output Excel file to be created",
                        default="hac-xform-{:%Y%m%d}.xlsx")
    parser.add_argument("-j", "--output-json", help="output JSON file to be created",
                        default="hac-xform-{:%Y%m%d}.json")                        
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
    logging.info("HAC GPS Points Loader started, with DEBUG environment variable value set to {}".format(repr(DEBUG)))
    HAC_gpsPoints.loadFromCsvFile(args.gps_csv_file)

    if False:
        rdg = HAC_gpsPoints.recordDataGenerator()
        for item in rdg:
            logging.info("item: {}".format(json.dumps(item)))
            models.mjesto_add(item)

    routeList = models.mjesto_get_unique_routes()
    for obj in routeList:
        route = obj[0]
        count = obj[1]
        if count > 1:        
            objlist = models.mjesto_get_list_by_route(route)
#            logging.info("route {} mjesta: {}".format(route, json.dumps([item.obj_to_dict() for item in objlist])))
            logging.info("route {} mjesta: {}".format(route, len(objlist)))
            comb = 0
            # make the matrix of (N) x (N-1) all combinations of entry and exit for a trip on that route
            for j, vj in enumerate(objlist):
                for k, vk in enumerate(objlist):
                    # exclude zero-length paths
                    if j == k:
                        continue
                    # exclude impossible paths
                    if vj.id_ulaz is None or vk.id_izlaz is None:
                        continue
                    # explicitly exclude some impossible combinations
                    if vj.mjesto == 'Zagreb' and vk.mjesto == 'Zagreb (Demerje)':
                        continue
                    if vj.mjesto == 'Bregana' or vk.mjesto == 'Bregana':
                        continue
                    comb += 1

                    logging.debug("combination {}: from '{}' to '{}'".format(comb, vj.mjesto, vk.mjesto))
                    models.routetab_add(vj.id, vk.id)

    db.session.commit()
    db.session.remove()
    logging.info("HAC GPS Points Loader finished")

    # TODO: what remains to be done now is to run TomTom API in a loop and update route matrix
    # TODO: this to be done in a separate tool which is able to pick up work and continue

    return 0

if __name__ == "__main__":
    sys.exit(main())
