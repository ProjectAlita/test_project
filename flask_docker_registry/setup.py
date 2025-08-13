"""
Setup script for Flask Docker Registry
"""

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='flask-docker-registry',
    version='0.1.0',
    description='Docker Registry HTTP API v2 implementation using Flask',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'flask-docker-registry=flask_docker_registry.__main__:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    python_requires='>=3.7',
)