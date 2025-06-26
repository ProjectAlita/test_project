from flask import Blueprint, jsonify

bp = Blueprint('api_v1', __name__)

@bp.route('/hello', methods=['GET'])
def hello():
    return jsonify({"ok": "hello"})

