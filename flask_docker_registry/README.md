# Flask Docker Registry

A Docker Registry HTTP API v2 implementation using Flask. This project allows you to run your own private Docker registry with authentication support.

## Features

- Implements the Docker Registry HTTP API v2 specification
- Supports Docker login, push, and pull operations
- Simple authentication mechanism (Basic Auth)
- Local filesystem storage for Docker images
- Support for Docker manifests and blobs
- Repository and tag listing

## Requirements

- Python 3.7+
- Flask
- PyJWT

## Installation

### From Source

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/flask-docker-registry.git
   cd flask-docker-registry
   ```

2. Install the package:
   ```
   pip install -e .
   ```

### Using pip

```
pip install flask-docker-registry
```

## Usage

### Starting the Registry

Run the registry with default settings:

```
flask-docker-registry
```

This will start the registry on `0.0.0.0:5000` with default authentication (username: `admin`, password: `password`).

### Command-line Options

```
usage: flask-docker-registry [-h] [--host HOST] [--port PORT] [--storage STORAGE]
                            [--auth-enabled] [--no-auth] [--username USERNAME]
                            [--password PASSWORD] [--debug]

Flask Docker Registry

optional arguments:
  -h, --help           show this help message and exit
  --host HOST          Host to bind to (default: 0.0.0.0)
  --port PORT          Port to bind to (default: 5000)
  --storage STORAGE    Storage path (default: ./storage)
  --auth-enabled       Enable authentication (default)
  --no-auth            Disable authentication
  --username USERNAME  Authentication username (default: admin)
  --password PASSWORD  Authentication password (default: password)
  --debug              Enable debug mode
```

### Environment Variables

You can also configure the registry using environment variables:

- `STORAGE_PATH`: Path to store registry data (default: `./storage`)
- `AUTH_ENABLED`: Enable authentication (default: `true`)
- `AUTH_USER`: Authentication username (default: `admin`)
- `AUTH_PASSWORD`: Authentication password (default: `password`)
- `AUTH_TOKEN_EXPIRY`: Token expiry in seconds (default: `3600`)

## Docker Client Integration

### Setting Up Insecure Registry

By default, Docker requires HTTPS for registry communication. For development/testing purposes, you can configure Docker to allow insecure registry connections:

1. Edit `/etc/docker/daemon.json` (create if it doesn't exist):
   ```json
   {
     "insecure-registries": ["localhost:5000"]
   }
   ```

2. Restart Docker:
   ```
   sudo systemctl restart docker
   ```

### Docker Login

```
docker login localhost:5000
```

Enter the username and password configured for the registry.

### Push an Image

```
# Tag an existing image
docker tag ubuntu:latest localhost:5000/myubuntu:latest

# Push to your registry
docker push localhost:5000/myubuntu:latest
```

### Pull an Image

```
docker pull localhost:5000/myubuntu:latest
```

### List Available Repositories

```
curl -X GET http://localhost:5000/v2/_catalog
```

### List Tags for a Repository

```
curl -X GET http://localhost:5000/v2/myubuntu/tags/list
```

## Production Deployment

For production use, it is highly recommended to:

1. Use HTTPS (TLS) to secure the registry
2. Set up proper authentication with strong passwords
3. Use a reverse proxy (like Nginx)
4. Configure proper storage backends
5. Set up proper user management

## License

MIT