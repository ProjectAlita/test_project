"""
Routes for Docker Registry HTTP API v2
"""

import hashlib
import json
import os
import re
from uuid import uuid4

from flask import (
    current_app, request, Response, jsonify, send_file, 
    make_response, stream_with_context, g
)

from flask_docker_registry.api.v2 import bp
from flask_docker_registry.auth import require_auth, authenticate_request, generate_token
from flask_docker_registry.storage import Storage


# Create storage instance for use in routes
@bp.before_request
def before_request():
    g.storage = Storage()


@bp.route('/')
@require_auth
def api_v2_base():
    """
    Base endpoint to verify that the API is implemented and available
    
    Returns:
        Empty response with 200 OK status
    """
    return jsonify({})


@bp.route('/auth', methods=['GET'])
def auth():
    """
    Authentication endpoint for Docker login
    
    Returns:
        JSON response with token
    """
    # Get credentials from basic auth header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return Response(
            json.dumps({"errors": [{"code": "UNAUTHORIZED", "message": "Authentication required"}]}),
            status=401,
            content_type='application/json'
        )
        
    # Validate credentials
    is_authenticated, _ = authenticate_request()
    if not is_authenticated:
        return Response(
            json.dumps({"errors": [{"code": "UNAUTHORIZED", "message": "Invalid credentials"}]}),
            status=401,
            content_type='application/json'
        )
        
    # Get required parameters
    service = request.args.get('service', 'registry')
    scope = request.args.get('scope', '')
    
    # Generate token
    token = generate_token(current_app.config['AUTH_USER'])
    
    return jsonify({
        "token": token,
        "expires_in": current_app.config['AUTH_TOKEN_EXPIRY'],
        "issued_at": "",  # Current time in ISO 8601 format (handled by Docker client)
    })


@bp.route('/<path:name>/blobs/uploads/', methods=['POST'])
@require_auth
def init_blob_upload(name):
    """
    Initialize a blob upload
    
    Args:
        name: Repository name
        
    Returns:
        Response with location header for upload
    """
    # Validate repository name
    if not re.match(r'^[a-z0-9]+(?:[._-][a-z0-9]+)*(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*$', name):
        return jsonify({
            "errors": [{"code": "NAME_INVALID", "message": f"Invalid repository name: {name}"}]
        }), 400
    
    # Initialize upload
    upload_id = g.storage.init_upload(name)
    
    # Handle mount parameter (copy existing blob)
    if request.args.get('mount') and request.args.get('from'):
        digest = request.args.get('mount')
        from_repo = request.args.get('from')
        
        # Check if blob exists in source repository
        if g.storage.blob_exists(digest):
            # Blob already exists, no need to upload
            return jsonify({}), 201, {'Location': f'/v2/{name}/blobs/{digest}'}
    
    # Return response with upload location
    location = f"/v2/{name}/blobs/uploads/{upload_id}"
    if request.args.get('digest'):
        location += f"?digest={request.args.get('digest')}"
    
    response = Response('', status=202)
    response.headers['Location'] = location
    response.headers['Range'] = '0-0'
    response.headers['Docker-Upload-UUID'] = upload_id
    
    return response


@bp.route('/<path:name>/blobs/uploads/<upload_id>', methods=['PATCH'])
@require_auth
def upload_blob_chunk(name, upload_id):
    """
    Upload a chunk of data for a blob
    
    Args:
        name: Repository name
        upload_id: Upload ID
        
    Returns:
        Response with updated range
    """
    # Get content range
    content_range = request.headers.get('Content-Range')
    if content_range:
        offset = int(content_range.split('-')[0])
    else:
        offset = None
    
    # Append data to upload
    new_offset = g.storage.append_upload(name, upload_id, request.data, offset)
    if new_offset < 0:
        return jsonify({
            "errors": [{"code": "BLOB_UPLOAD_INVALID", "message": "Invalid upload"}]
        }), 400
    
    # Return response with new range
    response = Response('', status=202)
    response.headers['Location'] = f"/v2/{name}/blobs/uploads/{upload_id}"
    response.headers['Range'] = f"0-{new_offset-1}"
    response.headers['Docker-Upload-UUID'] = upload_id
    
    return response


@bp.route('/<path:name>/blobs/uploads/<upload_id>', methods=['PUT'])
@require_auth
def complete_blob_upload(name, upload_id):
    """
    Complete a blob upload
    
    Args:
        name: Repository name
        upload_id: Upload ID
        
    Returns:
        Response with blob location
    """
    # Get digest
    digest = request.args.get('digest')
    if not digest:
        return jsonify({
            "errors": [{"code": "DIGEST_INVALID", "message": "Digest parameter missing"}]
        }), 400
    
    # Handle final chunk if provided
    if request.data:
        new_offset = g.storage.append_upload(name, upload_id, request.data)
        if new_offset < 0:
            return jsonify({
                "errors": [{"code": "BLOB_UPLOAD_INVALID", "message": "Invalid upload"}]
            }), 400
    
    # Complete upload
    stored_digest = g.storage.complete_upload(name, upload_id, digest)
    if not stored_digest:
        return jsonify({
            "errors": [{"code": "DIGEST_INVALID", "message": "Content does not match digest"}]
        }), 400
    
    # Return response with blob location
    response = Response('', status=201)
    response.headers['Location'] = f"/v2/{name}/blobs/{digest}"
    response.headers['Docker-Content-Digest'] = digest
    
    return response


@bp.route('/<path:name>/blobs/uploads/<upload_id>', methods=['DELETE'])
@require_auth
def cancel_blob_upload(name, upload_id):
    """
    Cancel a blob upload
    
    Args:
        name: Repository name
        upload_id: Upload ID
        
    Returns:
        Empty response
    """
    g.storage.cancel_upload(name, upload_id)
    return '', 204


@bp.route('/<path:name>/blobs/<digest>', methods=['HEAD'])
@require_auth
def check_blob(name, digest):
    """
    Check if blob exists
    
    Args:
        name: Repository name
        digest: Blob digest
        
    Returns:
        Empty response with blob size
    """
    blob, size = g.storage.get_blob(digest)
    if not blob:
        return jsonify({
            "errors": [{"code": "BLOB_UNKNOWN", "message": f"Blob {digest} unknown to registry"}]
        }), 404
    
    blob.close()
    
    response = Response('', status=200)
    response.headers['Content-Length'] = str(size)
    response.headers['Docker-Content-Digest'] = digest
    
    return response


@bp.route('/<path:name>/blobs/<digest>', methods=['GET'])
@require_auth
def get_blob(name, digest):
    """
    Get blob content
    
    Args:
        name: Repository name
        digest: Blob digest
        
    Returns:
        Blob content
    """
    blob, size = g.storage.get_blob(digest)
    if not blob:
        return jsonify({
            "errors": [{"code": "BLOB_UNKNOWN", "message": f"Blob {digest} unknown to registry"}]
        }), 404
    
    response = send_file(
        blob,
        as_attachment=True,
        download_name=digest.split(':')[1],
        mimetype='application/octet-stream'
    )
    
    response.headers['Docker-Content-Digest'] = digest
    return response


@bp.route('/<path:name>/manifests/<reference>', methods=['HEAD'])
@require_auth
def check_manifest(name, reference):
    """
    Check if manifest exists
    
    Args:
        name: Repository name
        reference: Tag or digest
        
    Returns:
        Empty response with manifest info
    """
    manifest, digest = g.storage.get_manifest(name, reference)
    if not manifest:
        return jsonify({
            "errors": [{"code": "MANIFEST_UNKNOWN", "message": f"Manifest {reference} unknown to registry"}]
        }), 404
    
    # Determine media type
    media_type = manifest.get('mediaType', 'application/vnd.docker.distribution.manifest.v2+json')
    
    response = Response('', status=200)
    response.headers['Content-Type'] = media_type
    response.headers['Docker-Content-Digest'] = digest
    response.headers['Content-Length'] = str(len(json.dumps(manifest, sort_keys=True).encode('utf-8')))
    
    return response


@bp.route('/<path:name>/manifests/<reference>', methods=['GET'])
@require_auth
def get_manifest(name, reference):
    """
    Get manifest content
    
    Args:
        name: Repository name
        reference: Tag or digest
        
    Returns:
        Manifest content
    """
    manifest, digest = g.storage.get_manifest(name, reference)
    if not manifest:
        return jsonify({
            "errors": [{"code": "MANIFEST_UNKNOWN", "message": f"Manifest {reference} unknown to registry"}]
        }), 404
    
    # Determine media type
    media_type = manifest.get('mediaType', 'application/vnd.docker.distribution.manifest.v2+json')
    
    response = jsonify(manifest)
    response.headers['Docker-Content-Digest'] = digest
    response.headers['Content-Type'] = media_type
    
    return response


@bp.route('/<path:name>/manifests/<reference>', methods=['PUT'])
@require_auth
def put_manifest(name, reference):
    """
    Upload manifest
    
    Args:
        name: Repository name
        reference: Tag or digest
        
    Returns:
        Empty response with manifest location
    """
    try:
        manifest_data = request.json
    except:
        return jsonify({
            "errors": [{"code": "MANIFEST_INVALID", "message": "Invalid manifest format"}]
        }), 400
    
    # Validate manifest
    if not isinstance(manifest_data, dict):
        return jsonify({
            "errors": [{"code": "MANIFEST_INVALID", "message": "Invalid manifest format"}]
        }), 400
    
    # Store manifest
    digest = g.storage.store_manifest(name, reference, manifest_data)
    
    response = Response('', status=201)
    response.headers['Location'] = f"/v2/{name}/manifests/{reference}"
    response.headers['Docker-Content-Digest'] = digest
    
    return response


@bp.route('/<path:name>/manifests/<reference>', methods=['DELETE'])
@require_auth
def delete_manifest(name, reference):
    """
    Delete manifest
    
    Args:
        name: Repository name
        reference: Tag or digest
        
    Returns:
        Empty response
    """
    if g.storage.delete_manifest(name, reference):
        return '', 202
    else:
        return jsonify({
            "errors": [{"code": "MANIFEST_UNKNOWN", "message": f"Manifest {reference} unknown to registry"}]
        }), 404


@bp.route('/_catalog', methods=['GET'])
@require_auth
def get_catalog():
    """
    List repositories
    
    Returns:
        List of repositories
    """
    n = request.args.get('n', type=int)
    last = request.args.get('last', '')
    
    repositories = g.storage.list_repositories()
    
    # Handle pagination
    if last:
        try:
            start_idx = repositories.index(last) + 1
            repositories = repositories[start_idx:]
        except ValueError:
            pass
    
    if n is not None and n > 0:
        result = repositories[:n]
        if len(repositories) > n:
            next_url = f"/v2/_catalog?n={n}&last={result[-1]}"
            response = jsonify({"repositories": result})
            response.headers['Link'] = f'<{next_url}>; rel="next"'
            return response
    else:
        result = repositories
    
    return jsonify({"repositories": result})


@bp.route('/<path:name>/tags/list', methods=['GET'])
@require_auth
def list_tags(name):
    """
    List tags for repository
    
    Args:
        name: Repository name
        
    Returns:
        List of tags
    """
    n = request.args.get('n', type=int)
    last = request.args.get('last', '')
    
    tags = g.storage.list_tags(name)
    if not tags and not g.storage.manifest_exists(name, ''):
        return jsonify({
            "errors": [{"code": "NAME_UNKNOWN", "message": f"Repository {name} not found"}]
        }), 404
    
    # Handle pagination
    if last:
        try:
            start_idx = tags.index(last) + 1
            tags = tags[start_idx:]
        except ValueError:
            pass
    
    if n is not None and n > 0:
        result = tags[:n]
        if len(tags) > n:
            next_url = f"/v2/{name}/tags/list?n={n}&last={result[-1]}"
            response = jsonify({"name": name, "tags": result})
            response.headers['Link'] = f'<{next_url}>; rel="next"'
            return response
    else:
        result = tags
    
    return jsonify({"name": name, "tags": result})