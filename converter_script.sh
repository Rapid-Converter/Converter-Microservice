#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define Docker image names and versions
CONVERTER_SERVICE_IMAGE="akshat315/converter-service:latest"

# Define container names
CONVERTER_CONTAINER="converter-service"

# Define ports
CONVERTER_PORT=8000

# Define Docker network (optional for inter-service communication)
DOCKER_NETWORK="app-network"

# Check if Docker network exists, if not, create it
if [ -z "$(docker network ls --filter name=^${DOCKER_NETWORK}$ --format="{{ .Name }}")" ]; then
    echo "Creating Docker network: ${DOCKER_NETWORK}"
    docker network create ${DOCKER_NETWORK}
fi

# Stop and remove existing containers if they exist
echo "Stopping existing containers if any..."

docker stop -f ${CONVERTER_CONTAINER} > /dev/null 2>&1 || true


# Run the Converter Service container
echo "Starting Converter Service..."
docker run -d \
    --name ${CONVERTER_CONTAINER} \
    --network ${DOCKER_NETWORK} \
    -p ${CONVERTER_PORT}:8000 \
    -e OUTPUT_DIR=/app/files \
    -e ENCRYPTION_SERVICE_URL=http://encryption-service:8001/encrypt \
    ${CONVERTER_SERVICE_IMAGE}

echo "Container is up and running."

# Optional: Display running containers
docker ps --filter "name=${CONVERTER_CONTAINER}" --filter "name=${ENCRYPTION_CONTAINER}"
