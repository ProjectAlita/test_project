"""
Authentication module for Docker Registry
"""

import base64
import hashlib
import hmac
import json
import time
from functools import wraps
from urllib.parse import quote_plus

import jwt
from flask import current_app, request, Response, jsonify


def authenticate_request():
    """
    Check if the request is authenticated
    
    Returns:
        Tuple of (is_authenticated, error_response)
    """
    if not current_app.config['AUTH_ENABLED']:
        return True, None
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False, _get_auth_challenge()
    
    auth_type, auth_value = auth_header.split(' ', 1)
    
    if auth_type.lower() == 'basic':
        return _check_basic_auth(auth_value)
    elif auth_type.lower() == 'bearer':
        return _check_bearer_auth(auth_value)
    
    return False, _get_auth_challenge()


def _check_basic_auth(auth_value):
    """
    Check Basic authentication value
    
    Args:
        auth_value: Base64 encoded username:password
        
    Returns:
        Tuple of (is_authenticated, error_response)
    """
    try:
        decoded = base64.b64decode(auth_value).decode('utf-8')
        username, password = decoded.split(':', 1)
        
        if username == current_app.config['AUTH_USER'] and password == current_app.config['AUTH_PASSWORD']:
            return True, None
    except Exception:
        pass
    
    return False, _get_auth_challenge()


def _check_bearer_auth(token):
    """
    Check Bearer token
    
    Args:
        token: JWT token
        
    Returns:
        Tuple of (is_authenticated, error_response)
    """
    try:
        secret = current_app.config['AUTH_PASSWORD']
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        
        if 'exp' in payload and payload['exp'] > time.time():
            return True, None
    except Exception:
        pass
    
    return False, _get_auth_challenge()


def _get_auth_challenge():
    """
    Generate HTTP 401 authentication challenge response
    
    Returns:
        Response object with WWW-Authenticate header
    """
    realm = f"http://{request.host}/v2/auth"
    service = "registry"
    scope = f"repository:{request.path.split('/')[2] if len(request.path.split('/')) > 2 else '*'}:pull,push"
    
    headers = {
        'WWW-Authenticate': f'Basic realm="{realm}"',
        'Docker-Distribution-Api-Version': 'registry/2.0'
    }
    
    return Response(
        json.dumps({"errors": [{"code": "UNAUTHORIZED", "message": "Authentication required"}]}),
        status=401,
        headers=headers,
        content_type='application/json'
    )


def require_auth(func):
    """
    Decorator to require authentication for a route
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        is_authenticated, error_response = authenticate_request()
        if not is_authenticated:
            return error_response
        return func(*args, **kwargs)
    
    return decorated


def generate_token(username):
    """
    Generate JWT token for authenticated user
    
    Args:
        username: Authenticated username
        
    Returns:
        JWT token string
    """
    expiry = int(time.time()) + current_app.config['AUTH_TOKEN_EXPIRY']
    payload = {
        'sub': username,
        'iss': 'flask-docker-registry',
        'iat': int(time.time()),
        'exp': expiry
    }
    
    return jwt.encode(payload, current_app.config['AUTH_PASSWORD'], algorithm='HS256')