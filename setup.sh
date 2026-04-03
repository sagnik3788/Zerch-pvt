#!/bin/bash

set -e

echo "=================================="
echo "  Zerch Docker Setup Script"
echo "=================================="

if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker installed!"
    exit 0
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed!"
fi

echo ""
echo "Versions:"
docker --version
docker-compose --version

echo ""
echo "Building Docker images..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 60

echo ""
echo "Service Status:"
docker-compose ps

echo ""
if curl -s http://localhost:8080/health > /dev/null; then
    echo "API is healthy"
else
    echo "API health check failed (it may still be starting)"
fi

echo ""
echo "Deployment Complete!"
echo "=================================="
echo "Access Points:"
echo "   UI:    http://localhost"
echo "   API:   http://localhost:8080"
echo ""
echo "Default Credentials:"
echo "   Email:    admin@123.com"
echo "   Password: admin123"
echo ""
echo "Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "=================================="
