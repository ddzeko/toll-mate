# views.py

from os import environ, path

import logging
from flask import request, json, jsonify, render_template, redirect, url_for, abort, flash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.datastructures import ImmutableMultiDict

from . import app, db, models
from tomtomLookup import tomtom_url, TomTomLookup

ttl = TomTomLookup() # global



@app.route('/', methods=['GET'])
def index():
    nxt = ','.join(f'.{ext}' for ext in app.config['UPLOAD_EXTENSIONS'])
    logging.debug("/ => upload_extensions = {} ==> {}".format(repr(app.config['UPLOAD_EXTENSIONS']), nxt))
    return render_template("index.html", upload_extensions=nxt) 

@app.route('/upload', methods=['GET'])
def upload_page():
    nxt = ','.join(f'.{ext}' for ext in app.config['UPLOAD_EXTENSIONS'])
    logging.debug("/upload => upload_extensions = {} ==> {}".format(repr(app.config['UPLOAD_EXTENSIONS']), nxt))
    return render_template("index.html", upload_extensions=nxt) 

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if 'Accept' in request.headers and request.headers['Accept'] == 'application/json':
        app.logger.debug("Request form\n-------\n%s",
                         pprint.pprint(request.form))
        app.logger.debug("Request files\n-------\n%s",
                         pprint.pprint(request.files))
        return r'{"result":"okie"}'

    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('upload_page'))


#   app.logger.debug("1-Request Method: '%s', headers:\n%s\n", request.method, request.headers)
#   app.logger.debug("2-Request form\n-------\n%s\n", request.form)
#   app.logger.debug("3-Request files\n-------\n%s\n", request.files)

    for rf in request.files:
        app.logger.debug(f'RF {rf}')

#   for ra in request.form:
#      app.logger.debug(f'RA {ra}')

    if request.method == 'POST':
        uploaded_file = request.files['file']
        xuf = uploaded_file.__dict__
#      app.logger.debug("TRACE\n-------\n%s\n", pprint.pprint(xuf))

        filename = secure_filename(uploaded_file.filename)
        app.logger.debug("FILENAME = %s\n", filename)
        app.logger.debug("CntType = %s\n", uploaded_file.content_type)

        if filename != '':
            (basename, file_ext) = path.splitext(filename)
            if file_ext[1:] not in app.config['UPLOAD_EXTENSIONS']:
                flash('Wrong type of file: ' + file_ext)
                return redirect(url_for('upload_page'))
#            abort(400)

        uploaded_file.save(path.join(
            app.config['UPLOAD_FOLDER'], filename.lower()))
        return r'{"result":"fileAccepted"}'


@app.errorhandler(RequestEntityTooLarge)
def handle_over_max_file_size(error):
    print("werkzeug.exceptions.RequestEntityTooLarge")
    return r'{"result":"exceptions.RequestEntityTooLarge"}'



@app.route('/hello', methods=['GET'])
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
