from flask_restful import Resource

from pylon.core.tools import log
from flask import request

# from ...models.metadata import MetadataEntry


class API(Resource):
    """ API implementation """

    url_params = [
        '',
        '<string:key>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, key=None):
        """ List all metadata keys or get metadata vales for specific key """
        if key is None:
            return []  # TODO: list present keys
        # TODO: get data for key
        return {"error": "not implemented yet"}, 418
    
    def post(self, key=None):
        """
        Echo back posted data. If key is provided, include key in response.
        """
        data = request.get_json(silent=True)
        if data is None:
            data = request.get_data(as_text=True)
        if key:
            return {"key": key, "data": data}, 200
        return data, 200
