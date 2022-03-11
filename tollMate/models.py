# models.py
import re
from . import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(120), unique=True)

    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __repr__(self):
        return f'<User {self.name!r}>'



class UlazIzlaz(db.Model):
    __tablename__ = 'hac_ulaz_izlaz'
    id = db.Column(db.Integer, primary_key=True)
    mjesto = db.Column(db.String(50), unique=True)
    gps_ul_lon = db.Column(db.Numeric(precision=10, scale=7), nullable=True)
    gps_ul_lat = db.Column(db.Numeric(precision=10, scale=7), nullable=True)
    gps_iz_lon = db.Column(db.Numeric(precision=10, scale=7), nullable=True)
    gps_iz_lat = db.Column(db.Numeric(precision=10, scale=7), nullable=True)

    def __init__(self, mjesto=None, gps_ulaz=None, gps_izlaz=None):
        self.mjesto = mjesto
        if gps_ulaz:
            (lon, lat) = re.split(', ?', gps_ulaz)
            self.gps_ul_lon = lon
            self.gps_ul_lat = lat
        if gps_izlaz:
            (lon, lat) = re.split(', ?', gps_izlaz)
            self.gps_iz_lon = lon
            self.gps_iz_lat = lat

    def __repr__(self):
        return f'<UlazIzlaz {self.mjesto!r}>'
