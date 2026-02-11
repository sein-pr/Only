#!/bin/bash

# Shopy Application Startup Script
echo "🚀 Starting Shopy Application..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. You can edit it to customize your settings."
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down

# Build and start the application
echo "🔨 Building and starting the application..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Initialize database if needed
echo "🗄️ Initializing database..."
docker-compose exec -T web python -c "
from app import app, db
with app.app_context():
    try:
        db.create_all()
        print('✅ Database initialized successfully!')
    except Exception as e:
        print(f'⚠️ Database initialization: {e}')
"

echo ""
echo "🎉 Shopy Application is now running!"
echo ""
echo "📱 Access your application at:"
echo "   • Main Application: http://localhost:80"
echo "   • Direct Flask App: http://localhost:5000"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs: docker-compose logs -f"
echo "   • Stop app: docker-compose down"
echo "   • Restart app: docker-compose restart"
echo ""
echo "📊 To share with others:"
echo "   1. Find your computer's IP address"
echo "   2. Share: http://YOUR_IP_ADDRESS:80"
echo "   3. Make sure your firewall allows port 80"
echo ""
echo "Happy shopping! 🛒"
