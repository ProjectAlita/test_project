from flask_restful import Resource
from flask import request
from pydantic import ValidationError

from pylon.core.tools import log
from ...models.metadata import MetadataEntry
from ...models.pd.metadata import MetadataKeyResponse, MetadataDataResponse, MetadataValidatorModel


def check_key_param(func):
    def wrap(*args, **kwargs):
        if not kwargs.get("key"):
            msg = "key is required."
            log.error(msg)
            return {"error": msg}, 400
        return func(*args, **kwargs)
    return wrap


class API(Resource):
    """ API implementation """

    url_params = [
        '',
        '<string:key>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, key: str | None = None):
        """ List all metadata keys or get metadata vales for specific key """
        if key is None:
            items = MetadataEntry.get_all()
            return [MetadataKeyResponse.from_orm(item).dict() for item in items], 200

        item = MetadataEntry.get_or_404(key)
        return MetadataDataResponse.from_orm(item).dict(), 200

    @check_key_param
    def post(self, key: str | None = None):
        """ Create metadata"""
        payload = request.get_json()
        payload["key"] = key

        try:
            MetadataValidatorModel.validate(payload)
        except ValidationError as e:
            return {'error': 'validation error', 'detail': e.errors()}, 400

        if MetadataEntry.get_by_key(key):
            return {"error": "key already exists."}, 400

        item = MetadataEntry(**payload)
        item.insert()
        return MetadataDataResponse.from_orm(item).dict(), 201

    @check_key_param
    def put(self, key: str | None = None):
        """ Update metadata"""
        payload = request.get_json()
        payload["key"] = key

        try:
            MetadataValidatorModel.validate(payload)
        except ValidationError as e:
            return {'error': 'validation error', 'detail': e.errors()}, 400

        item = MetadataEntry.put(key, payload["data"])
        return MetadataDataResponse.from_orm(item).dict(), 200

    @check_key_param
    def delete(self, key: str | None = None):
        """ Delete metadata"""
        if item := MetadataEntry.get_or_404(key):
            item.delete()
            return {"message": "successfully deleted"}, 204
