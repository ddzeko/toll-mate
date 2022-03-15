# views.py

import logging
from flask import abort, request, json, jsonify
from . import app, db, models
from tomtomLookup import tomtom_url

@app.route('/')
def hello_world():
    try:
        return f'Hello from tollMate-view!'
    except Exception as e:
            logging.error (e.__class__.__name__)
            db.session.rollback ()
            abort (500, 'Error. Something bad happened.')



@app.route('/tom/<route_id>', methods=['GET'])
def show_tomtom_url(route_id):
    gps_coords = [ str(item) for item in models.routetab_get_by_id(route_id) ]
    logging.info("gpsVector = {}".format(gps_coords))
    return tomtom_url(gps_coords[0:2], gps_coords[2:4])

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

