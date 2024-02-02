from flask_restful import Resource

from pylon.core.tools import log

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
