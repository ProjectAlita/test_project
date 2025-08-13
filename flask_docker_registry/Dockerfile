FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package
RUN pip install -e .

# Create storage directory
RUN mkdir -p /var/lib/registry

# Expose port
EXPOSE 5000

# Set environment variables
ENV STORAGE_PATH=/var/lib/registry
ENV AUTH_ENABLED=true
ENV AUTH_USER=admin
ENV AUTH_PASSWORD=password

# Run application
CMD ["flask-docker-registry", "--host", "0.0.0.0", "--port", "5000"]