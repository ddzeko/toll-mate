#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @author Copyright (c) 2022 Damir Dzeko Antic
# @license MIT No Attribution
# @version 0.1.2
# @lastUpdate 2022-02-05

# ChangeLog:
# - can be tested with: python3 -m unittest tomtomLookup.py
# - added object destructor to close the session/socket


import sys
try:
    assert (sys.version_info.major == 3 and sys.version_info.minor >= 7), "Python version must be 3.7 or newer"
except Exception as e:
    print (e)
    sys.exit(1)

import time
from os import environ
from datetime import timedelta

from requests_cache import CachedSession
import unittest
import json


TOMTOM_AUTH_KEY = environ.get("TOMTOM_AUTH_KEY")

def tomtom_url(gps_od, gps_do):
    def prefix():
        return 'https://api.tomtom.com/routing/1/calculateRoute/'
    def suffix():
        return (f'/json?key={TOMTOM_AUTH_KEY}&routeRepresentation=summaryOnly&maxAlternatives=0' + 
                '&computeTravelTimeFor=none&routeType=fastest&traffic=false&travelMode=car')
    return f'{prefix()}{",".join(gps_od)}:{",".join(gps_do)}{suffix()}'


class TomTomLookup():

    def _make_throttle_hook(timeout=1.0):
        """Make a request hook function that adds a custom delay for non-cached requests"""
        def hook(response, *args, **kwargs):
            if not getattr(response, 'from_cache', False):
                # print('sleeping')
                time.sleep(timeout)
            return response
        return hook

    def __init__(self):
        session = CachedSession('./requests_cache.db', 
            backend='sqlite', 
            timeout=30, 
            expire_after=timedelta(days=30),
            old_data_on_error=True,
            serializer='json')
        session.hooks['response'].append(TomTomLookup._make_throttle_hook(1.25))
        self.session = session

    def getUrl(self, url):
        response = self.session.get(url)
        if response.status_code != 200:
            raise Exception("TomTomLookup: GET call returned invalid response")
        return response.text

    def getDistance(self, url):
        response_text = self.getUrl(url)
        try:
            json_obj = json.loads(response_text)
            return json_obj['routes'][0]['summary']['lengthInMeters']
        except:
            raise Exception("TomTomLookup: Failed to decode REST API response")

    def __del__(self):
        self.session.close()

class TestTomTomLookup(unittest.TestCase):
    def setUp(self):
        self.tomtom = TomTomLookup()

    def test_one_url(self):
        response_text = self.tomtom.getUrl('http://httpbin.org/delay/3')
        response_obj = json.loads(response_text)
        self.assertTrue(response_obj['url'] is not None)


def main():
    print(f'{__file__} should not be run as stand-alone program')
    return 2

if __name__ == '__main__':
    sys.exit(main())