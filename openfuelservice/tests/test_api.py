import json
import unittest
from pathlib import Path

from flask import request

from openfuelservice.tests import client

test_resources = Path(__file__).parent.joinpath('resources')
simple_cfd_filter = json.loads('{"data_source": "cfd","fuel_type": "gasoline","vehicle_type": "car","driving_style": '
                               '"fast",''"vehicle_categories": ["all"]}')


class TestAPIPost(unittest.TestCase):
    def test_simple_route_request(self):
        global simple_cfd_filter
        with open(test_resources.joinpath('geojson_route_geometry.json'), 'rb') as f:
            geojson = json.load(f)
        # simple_cfd_filter['tank_sizes'] = '{"a": "100"}'
        # simple_cfd_filter['fuel_consumptions'] = '{"a": "4.5"}'
        # simple_cfd_filter['request_id'] = 'test123'
        # simple_cfd_filter['driving_speed'] = '60'
        request_json = {
            'request': 'route',
            'geometry': {
                'geojson': geojson,
                'filters': simple_cfd_filter
            }
        }
        response: request = client.post('/fuel?request=route', json=request_json)
        json_response = json.loads(response.data)
        self.assertIn('attributions', json_response)
        self.assertIn('fuel_stats', json_response)
        self.assertIn('general', json_response)


class TestAPIGetter(unittest.TestCase):
    def test_categories_validity(self):
        response: request = client.get('/fuel?request=categories')
        valid_response = response.status_code
        byte_data = response.data
        json_data = json.loads(byte_data)
        self.assertEqual(valid_response, 200)
        self.assertNotEqual(len(byte_data), 0)
        self.assertIn(b'categories', byte_data)
        self.assertIn('categories', json_data)
        self.assertGreater(len(json_data['categories']), 0)
        assert b'{"categories": {"a": {"de": "Kleinstwagen", "en": "mini cars", "short": "a"}, "b": {"de": ' \
               b'"Kleinwagen", "en": "small cars", "short": "b"}, "c": {"de": "Mittelklasse", "en": "medium cars", ' \
               b'"short": "c"}, "d": {"de": "Obere Mittelklasse", "en": "large cars", "short": "d"}, "e": {"de": ' \
               b'"Oberklasse", "en": "executive cars", "short": "e"}, "f": {"de": "Luxusklasse", "en": "luxury cars", ' \
               b'"short": "f"}, "j": {"de": "SUV", "en": "SUV", "short": "j"}, "lcv": {"de": "Nutzfahrzeuge", ' \
               b'"en": "Utilities", "short": "lcv"}, "m": {"de": "Van", "en": "MiniVaN - multi purpose cars", ' \
               b'"short": "m"}, "pu": {"de": "Pick-up", "en": "Pick-up", "short": "pu"}, "s": {"de": "Sportwagen", ' \
               b'"en": "sport coup\\u00e9s", "short": "s"}}}' in byte_data

    def test_ec_brands_validity(self):
        response: request = client.get('/fuel?request=brands&filter=ec')
        valid_response = response.status_code
        byte_data = response.data
        json_data = json.loads(byte_data)
        self.assertEqual(valid_response, 200)
        self.assertNotEqual(len(byte_data), 0)
        self.assertIn(b'brands', byte_data)
        self.assertIn('brands', json_data)
        self.assertGreater(len(json_data['brands']), 0)

    def test_cfd_brands_validity(self):
        response: request = client.get('/fuel?request=brands&filter=cfd')
        valid_response = response.status_code
        byte_data = response.data
        json_data = json.loads(byte_data)
        self.assertEqual(valid_response, 200)
        self.assertNotEqual(len(byte_data), 0)
        self.assertIn(b'brands', byte_data)
        self.assertIn('brands', json_data)
        self.assertGreater(len(json_data['brands']), 0)
