# models.py
from operator import and_
import re
from . import db
from sqlalchemy import and_, inspect
from sqlalchemy.sql import func
from sqlalchemy.types import JSON
from sqlalchemy.orm import aliased
import logging

class UploadFiles(db.Model):
    __tablename__ = 'upload_files'
    id = db.Column(db.Integer, primary_key=True)
    orig_filename = db.Column(db.String(50), unique=True)
    dest_filename = db.Column(db.String(120), unique=True)
    updated_at    = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    created_at    = db.Column(db.DateTime, default=func.now())
    status        = db.Column(db.Integer, nullable=False, default=0)
    from_remoteip = db.Column(db.String(50), nullable=True)
    from_useragent = db.Column(db.String(250), nullable=True)
    
    def __init__(self, orig_filename=None, dest_filename=None, from_remoteip=None, from_useragent=None):
        self.orig_filename = orig_filename
        self.dest_filename = dest_filename
        self.from_remoteip = from_remoteip
        self.from_useragent = from_useragent

    def __repr__(self):
        return f'<UploadFiles {self.dest_filename!r}>'


class TripRecords(db.Model):
    __tablename__ = 'trip_records'
    id = db.Column(db.Integer, primary_key=True)
    id_upload = db.Column(db.Integer, db.ForeignKey('upload_files.id', name="fk_upload"))    
    entered_at  = db.Column(db.DateTime, nullable=False)
    exited_at   = db.Column(db.DateTime, nullable=False)
    id_mjesto_od = db.Column(db.Integer, db.ForeignKey('hac_mjesto.id', use_alter=True, name="fk_tr_mjesto_od"), nullable=False)
    id_mjesto_do = db.Column(db.Integer, db.ForeignKey('hac_mjesto.id', use_alter=True, name="fk_tr_mjesto_do"), nullable=False)
    status        = db.Column(db.Integer, nullable=False, default=0)
    hac_toll_hrk  = db.Column(db.Numeric(precision=6, scale=2), nullable=False)
    trip_length   = db.Column(db.Integer, nullable=True)
    
    def __init__(self, id_upload=None, entered_at=None, exited_at=None, hac_toll_hrk=None):
        self.id_upload = id_upload
        self.entered_at = entered_at
        self.exited_at = exited_at
        self.hac_toll_hrk = hac_toll_hrk  # will have to be changed to EUR at some point

    def __repr__(self):
        return f'<TripRecords {self.id!r}>'



class HAC_Point(db.Model):
    __tablename__ = 'hac_point'
    id = db.Column(db.Integer, primary_key=True)
    id_mjesto = db.Column(db.Integer, db.ForeignKey('hac_mjesto.id', name="fk_mjesto"))
    je_izlaz = db.Column(db.Boolean, nullable=False)
    gps_lon = db.Column(db.Numeric(precision=10, scale=7), nullable=False)
    gps_lat = db.Column(db.Numeric(precision=10, scale=7), nullable=False)
    updated_at    = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    created_at    = db.Column(db.DateTime, default=func.now())

    def __init__(self, id_mjesto=None, je_izlaz=None, gps_lon=None, gps_lat=None, gps_lon_lat=None):
        self.id_mjesto = id_mjesto
        self.je_izlaz = True if je_izlaz else False
        if gps_lon_lat:
            (lon, lat) = re.split(', ?', gps_lon_lat)
        else:
            (lon, lat) = (gps_lon, gps_lat)
        self.gps_lon = lon
        self.gps_lat = lat

    def __repr__(self):
        return f'<HAC_Point {self.id_mjesto!r}>'


class HAC_Mjesto(db.Model):
    __tablename__ = 'hac_mjesto'
    id = db.Column(db.Integer, autoincrement='ignore_fk', primary_key=True)
    mjesto = db.Column(db.String(50), unique=True)
    ruta = db.Column(db.String(15), nullable=False, default="")    
    id_ulaz = db.Column(db.Integer, db.ForeignKey('hac_point.id', use_alter=True, name="fk_point_ul"), nullable=True)
    id_izlaz = db.Column(db.Integer, db.ForeignKey('hac_point.id', use_alter=True, name="fk_point_iz"), nullable=True)
    updated_at    = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    created_at    = db.Column(db.DateTime, default=func.now())

    point_ul = db.relationship(HAC_Point, foreign_keys=[id_ulaz], 
        primaryjoin=id_ulaz==HAC_Point.id,
        post_update=True)

    point_iz = db.relationship(HAC_Point, foreign_keys=[id_izlaz],
        primaryjoin=id_izlaz==HAC_Point.id, 
        post_update=True)

    mjesto_in_point_ul = db.relationship(HAC_Point, foreign_keys=[HAC_Point.id_mjesto],
        primaryjoin=id==HAC_Point.id_mjesto, post_update=True)

    __table_args__ = (
        db.UniqueConstraint("id_ulaz", "id_izlaz", name="uc_ulaz_izlaz"),
    )

    def __init__(self, mjesto=None, ruta=None, id_ulaz=None, id_izlaz=None):
        self.mjesto = mjesto
        self.ruta = ruta
        self.id_ulaz = id_ulaz
        self.id_izlaz = id_izlaz

    def __repr__(self):
        return f'<HAC_Mjesto {self.mjesto!r}>'

    def obj_to_dict(self):  # for build json format
        return {
            "id": self.id,
            "mjesto": self.mjesto,
            "ruta": self.ruta
        }

class HAC_TablicaRuta(db.Model):
    __tablename__ = 'hac_tablica_ruta'
    id = db.Column(db.Integer, primary_key=True)
    id_mjesto_od = db.Column(db.Integer, db.ForeignKey('hac_mjesto.id', use_alter=True, name="fk_mjesto_od"), nullable=False)
    id_mjesto_do = db.Column(db.Integer, db.ForeignKey('hac_mjesto.id', use_alter=True, name="fk_mjesto_do"), nullable=False)
    updated_at    = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    created_at    = db.Column(db.DateTime, default=func.now())
    route_status = db.Column(db.SmallInteger, default=0)
    route_length = db.Column(db.Integer)      # travel distance obtained via TomTom API
    tomtom_response = db.Column(JSON)

# foreign_keys=[id_mjesto_od, id_mjesto_do], 
#    points = db.relationship(HAC_Mjesto, primaryjoin='and_(HAC_TablicaRuta.id_mjesto_od==HAC_Mjesto.id, HAC_TablicaRuta.id_mjesto_do==HAC_Mjesto.id)',
#        post_update=True)

#    point_iz = db.relationship(HAC_Mjesto, foreign_keys=[id_mjesto_do],
#        primaryjoin=id_mjesto_do==HAC_Mjesto.id, 
#        post_update=True)

    __table_args__ = (
        db.UniqueConstraint("id_mjesto_od", "id_mjesto_do", name="uc_mjesto_od_do"),
    )

    def __init__(self, id_mjesto_od=None, id_mjesto_do=None):
        self.id_mjesto_od = id_mjesto_od
        self.id_mjesto_do = id_mjesto_do


# adding HAC_Mjesto record and its entry/exit points as HAC_Point
def mjesto_add(item_dict):
    mj = HAC_Mjesto(mjesto=item_dict['mjesto'], ruta=item_dict['ruta'])
    db.session.add(mj)
    db.session.flush()
    for pt in ('ulaz', 'izlaz'):
        if pt in item_dict:
            print(f'PT={pt}')
            item_pt = item_dict[pt]
            je_izlaz = True if pt == 'izlaz' else False
            pto = HAC_Point(id_mjesto=mj.id, je_izlaz=je_izlaz, gps_lon=item_pt['lon'], gps_lat=item_pt['lat'])
            db.session.add(pto)
            db.session.flush()
            setattr(mj, f'id_{pt}', pto.id)
    db.session.commit()
    return mj.id


# add entry to matrix HAC_TablicaRuta
def mjesto_get_list_by_route(route):
    return db.session.query(HAC_Mjesto).filter_by(ruta=route).all()


def mjesto_get_unique_routes():
    return db.session.query(HAC_Mjesto.ruta, func.count(HAC_Mjesto.ruta)).group_by(HAC_Mjesto.ruta).all()

# adding HAC_TablicaRuta entry initially, will require processing to populate with distance
def routetab_add(id_mjesto_od, id_mjesto_do):
    tabEntry = HAC_TablicaRuta(id_mjesto_od, id_mjesto_do)
    db.session.add(tabEntry)
    db.session.commit()
    return tabEntry.id


# retrieval of GPS points of entry and exit needed for TomTom Routing API lookup
def routetab_get_by_id(route_id):
    p1s = (db.session.query(HAC_Mjesto.id_ulaz).join(HAC_TablicaRuta, HAC_Mjesto.id == HAC_TablicaRuta.id_mjesto_od)
            .filter(HAC_TablicaRuta.id == route_id).scalar())
    p2s = (db.session.query(HAC_Mjesto.id_izlaz).join(HAC_TablicaRuta, HAC_Mjesto.id == HAC_TablicaRuta.id_mjesto_do)
            .filter(HAC_TablicaRuta.id == route_id).scalar())
    return (
        db.session.query(HAC_Point.gps_lon, HAC_Point.gps_lat).filter(HAC_Point.id==p1s).first(),
        db.session.query(HAC_Point.gps_lon, HAC_Point.gps_lat).filter(HAC_Point.id==p2s).first()
    )   


def routetab_update(route_id, resp, dist):
    try:
        db.session.query(HAC_TablicaRuta).filter_by(id=route_id).update(
            {   "tomtom_response": resp,
                "route_length": dist,
                "route_status": 1
            })
        db.session.commit()
    except:
        print('Error in routetab_update()')

def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

# retrieval of descriptive details of HAC_Mjesto entity
def mjesto_get_by_id(mjesto_id):
    return object_as_dict(db.session.query(HAC_Mjesto).filter_by(id=mjesto_id).first())


# route info 
def routetab_get_routeinfo(hac_ulaz, hac_izlaz):
    logging.info("now in models.routetab_get_routeinfo ...")
    try:
        m1s = (db.session.query(HAC_Mjesto.id).filter(HAC_Mjesto.mjesto == hac_ulaz).scalar())
        m2s = (db.session.query(HAC_Mjesto.id).filter(HAC_Mjesto.mjesto == hac_izlaz).scalar())
        print("m1s={} m2s={}".format(m1s, m2s))
        routeInfo = (db.session.query(HAC_TablicaRuta.id, HAC_TablicaRuta.route_length)
            .filter(and_(HAC_TablicaRuta.id_mjesto_od == m1s, HAC_TablicaRuta.id_mjesto_do == m2s)).first())
        (route_id, route_length) = list(routeInfo)
        return { "route_length": route_length }
    except:
        print('Error in routetab_get_routeinfo()')
        return { "error": "Error in routetab_get_routeinfo()" }
