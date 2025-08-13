"""
Docker Registry HTTP API v2 implementation
"""

from flask import Blueprint

bp = Blueprint('v2', __name__, url_prefix='/v2')

from flask_docker_registry.api.v2 import routes