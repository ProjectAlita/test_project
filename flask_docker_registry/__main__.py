"""
Entry point for Flask Docker Registry
"""

import os
import sys
import argparse

from flask_docker_registry.app import create_app


def parse_args():
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Flask Docker Registry')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--storage', default=None, help='Storage path (default: ./storage)')
    parser.add_argument('--auth-enabled', action='store_true', help='Enable authentication (default)')
    parser.add_argument('--no-auth', dest='auth_enabled', action='store_false', help='Disable authentication')
    parser.add_argument('--username', default=None, help='Authentication username (default: admin)')
    parser.add_argument('--password', default=None, help='Authentication password (default: password)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    parser.set_defaults(auth_enabled=True)
    
    return parser.parse_args()


def main():
    """
    Main entry point
    """
    args = parse_args()
    
    # Update environment variables based on arguments
    if args.storage:
        os.environ['STORAGE_PATH'] = args.storage
    
    os.environ['AUTH_ENABLED'] = str(args.auth_enabled).lower()
    
    if args.username:
        os.environ['AUTH_USER'] = args.username
    
    if args.password:
        os.environ['AUTH_PASSWORD'] = args.password
    
    # Create and run application
    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    sys.exit(main())