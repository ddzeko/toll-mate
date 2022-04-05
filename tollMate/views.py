# views.py

from os import environ, path
import hashlib
from pprint import pprint
import logging
from datetime import datetime
from flask import request, json, jsonify, render_template, redirect, url_for, abort, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.datastructures import ImmutableMultiDict, FileStorage

from . import app, db, models
from .controllers.tomtomLookup import tomtom_url, TomTomLookup
from .controllers.hacTripsExcel import HAC_Sheet_Object

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


@app.route('/uploader', methods=['POST'])
def upload_file():

    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))


    logging.debug("1-Request Method: '%s', headers:\n%s\n", request.method, request.headers)
    logging.debug("2-Request form\n-------\n%s\n", request.form)
    logging.debug("3-Request files\n-------\n%s\n", request.files)

    uploaded_file = 'none-so-far'
    if request.method == 'POST':
        uploaded_files = request.files.getlist('file')
        logging.debug("4-getlist/files: %d\n", len(uploaded_files))
        for ufv in uploaded_files:
            logging.debug("xxx = %s\n", ufv)
            try:
                if isinstance(ufv, FileStorage) and ufv.filename:
                    uploaded_file = ufv
                    break
            except:
                pass

        logging.debug("TRACE\n-------\n%s\n", uploaded_file)

#    if 'Accept' in request.headers and request.headers['Accept'] == 'application/json':
#        app.logger.debug("Request form\n-------\n%s", pprint(request.form))
#        app.logger.debug("Request files\n-------\n%s", pprint(request.files))
#        return r'{"result":"okie"}'

#     ffd = request.files.to_dict(flat=False)
# #    logging.debug("0-FFD\n-------\n%s\n", pprint(ffd))

#     for rf in ffd:
#         logging.debug("RF>>> %s => %s\n<<<", rf, ffd[rf])
#         for ii in range(len(ffd[rf])):
#             logging.debug("RF %d >>> => %s\n<<<", ii, ffd[rf][ii])


    filename = secure_filename(uploaded_file.filename)
    
    # good logging goes to system default location
    app.logger.debug("FILENAME = %s\n", filename)
    app.logger.debug("MimeType = %s\n", uploaded_file.content_type)

    if filename != '':
        (basename, file_ext) = path.splitext(filename)
        if file_ext[1:] not in app.config['UPLOAD_EXTENSIONS']:
            flash('Wrong type of file: ' + file_ext)
            return redirect(url_for('upload_page'))
    else:
        abort(400)

    # generate safe and random local filename
    timestamp = datetime.now().isoformat()
    fn_with_tstamp = f'{filename}.{timestamp}'
    hash_object = hashlib.sha256(fn_with_tstamp.encode('utf-8'))
    hex_digest = hash_object.hexdigest()[:32]
    local_filename = f'{hex_digest}{file_ext}'
    json_filename = f'{hex_digest}.json'

    uploaded_file.save(path.join(
        app.config['UPLOAD_FOLDER'], local_filename))

    # add a record to uploads table
    uf_id = models.uploadfiles_add(
        orig_filename=filename,
        dest_filename=local_filename,
        from_remoteip=request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
        from_useragent=request.headers.get('User-Agent'))

    uploaded_xlsx = path.join(app.config['UPLOAD_FOLDER'], local_filename)
    datastore_json = path.join(app.config['DATASTORE_FOLDER'], json_filename)

    # for JSON literals
    true = True
    false = False
    null = None

    hac_sheet = HAC_Sheet_Object(uploads_id=uf_id, original_wb_fn=filename, hashed_wb_fn=uploaded_xlsx)
    tr_count = hac_sheet.process_workbook(datastore_json)
    
    if tr_count:
        return jsonify({
            "result": "fileAccepted",
            "success": true,
            "error": "none",
            "uploadFilesId": uf_id,
            "tripRecords_count": tr_count,
            "datastore_json": datastore_json
        })
    else:
        return jsonify({
            "result": "fileProcessingError",
            "success": false,
            "error": "unspecified error"
        })


@app.errorhandler(RequestEntityTooLarge)
def handle_over_max_file_size(error):
    print("werkzeug.exceptions.RequestEntityTooLarge")
    return r'{"result":"exceptions.RequestEntityTooLarge", "success": false, "error": "file too large"}'



@app.route('/hello', methods=['GET'])
def hello_world():
    try:
        return f'Hello from tollMate-view!'
    except Exception as e:
            logging.error (e.__class__.__name__)
            db.session.rollback ()
            abort (500, 'Error. Something bad happened.')


@app.route('/datastore/<path:filename>', methods=['GET'])
def datastore_show_item(filename):
    app.logger.debug("DS folder = '%s', filename = '%s'\n", app.config['DATASTORE_FOLDER'], filename)
    return send_from_directory(path.join('..', app.config['DATASTORE_FOLDER']), filename, as_attachment=True)
#    return f'Requested item: {file}'


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


@app.route('/api/mjesto', methods=['GET'])
def api_mjesto_get_id():
    args = request.args
    mjesto = args.get('mjesto')
    if mjesto is None:
        return   
    return jsonify(models.mjesto_get_by_mjesto(mjesto))


@app.route('/api/point', methods=['GET'])
def api_point_get_mjesto_port():
    args = request.args
    mjesto_id = args.get('mjestoId')
    port = args.get('port')
    if None in (mjesto_id, port):
        return
    return jsonify(models.point_get_by_mjesto_port(mjesto_id, port))



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
