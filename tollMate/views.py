# views.py

from os import environ

import logging
from flask import abort, request, json, jsonify
from . import app, db, models
from tomtomLookup import tomtom_url, TomTomLookup

ttl = TomTomLookup() # global


@app.route('/')
def hello_world():
    try:
        return f'Hello from tollMate-view!'
    except Exception as e:
            logging.error (e.__class__.__name__)
            db.session.rollback ()
            abort (500, 'Error. Something bad happened.')


# TOMTOM API

@app.route('/tom/url/<route_id>', methods=['GET'])
def show_tomtom_url(route_id):
    (od, do) = models.routetab_get_by_id(route_id)
    gps_od = [ str(item) for item in od ]
    gps_do = [ str(item) for item in do ]
    logging.info("gps_od = {}, gps_do = {}".format(gps_od, gps_do))
    return tomtom_url(gps_od, gps_do)


@app.route('/tom/run/<route_id>', methods=['GET'])
def fetch_tomtom_url(route_id):
    (od, do) = models.routetab_get_by_id(route_id)
    gps_od = [ str(item) for item in od ]
    gps_do = [ str(item) for item in do ]
    logging.info("gps_od = {}, gps_do = {}".format(gps_od, gps_do))
    url = tomtom_url(gps_od, gps_do)
    resp = ttl.getUrl(url)
    dist = ttl.getDistance_from_resp(resp)
    models.routetab_update(route_id, resp, dist)
    return jsonify({"route_length":dist})




# some API methods returning JSON

@app.route('/api/route/<route_id>', methods=['GET'])
def api_route_get_coords(route_id):
    return jsonify(models.routetab_get_by_id(route_id))

@app.route('/api/mjesto/<mjesto_id>', methods=['GET'])
def api_mjesto_get_details(mjesto_id):
    return jsonify(models.mjesto_get_by_id(mjesto_id))



@app.route('/post_json', methods=['POST'])
def process_json():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.get_json()
        return json
    else:
        return 'Content-Type not supported!'


@app.route('/api/routeInfo', methods=['POST'])
def process_routeinfo():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        # check input parameters are there
        json = request.get_json()
        if ('hac_ulaz' in json and 'hac_izlaz' in json):
            logging.info("Request to {} with parameters: hac_ulaz={}, hac_izlaz={}"
                .format(request.environ.get('REQUEST_URI'), repr(json['hac_ulaz']), repr(json['hac_izlaz'])))
            return jsonify(models.routetab_get_routeinfo(json['hac_ulaz'], json['hac_izlaz']))
        else:
            return "Parameters missing"
    else:
        return 'Content-Type not supported!'


@app.route('/api/osEnv', methods=['GET'])
def get_os_environment():
    rend = ""
    for item, value in environ.items():
        rend = rend + ('<br>{}: {}'.format(item, value))
    return rend

@app.route('/api/rqEnv', methods=['GET'])
def get_request_environment():
    rend = ""
    for item, value in request.environ.items():
        rend = rend + ('<br>{}: {}'.format(item, value))
    return rend
