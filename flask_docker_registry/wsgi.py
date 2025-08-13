"""
WSGI entry point for Flask Docker Registry
"""

from flask_docker_registry.app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()