@echo off
REM Shopy Application Startup Script for Windows

echo 🚀 Starting Shopy Application...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker first.
    echo Visit: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    echo Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env.example .env
    echo ✅ .env file created. You can edit it to customize your settings.
)

REM Stop any existing containers
echo 🛑 Stopping any existing containers...
docker-compose down

REM Build and start the application
echo 🔨 Building and starting the application...
docker-compose up --build -d

REM Wait for services to be ready
echo ⏳ Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo 🔍 Checking service status...
docker-compose ps

REM Initialize database if needed
echo 🗄️ Initializing database...
docker-compose exec -T web python -c "from app import app, db; app.app_context().push(); db.create_all(); print('✅ Database initialized successfully!')"

echo.
echo 🎉 Shopy Application is now running!
echo.
echo 📱 Access your application at:
echo    • Main Application: http://localhost:80
echo    • Direct Flask App: http://localhost:5000
echo.
echo 🔧 Useful commands:
echo    • View logs: docker-compose logs -f
echo    • Stop app: docker-compose down
echo    • Restart app: docker-compose restart
echo.
echo 📊 To share with others:
echo    1. Find your computer's IP address
echo    2. Share: http://YOUR_IP_ADDRESS:80
echo    3. Make sure your firewall allows port 80
echo.
echo Happy shopping! 🛒
pause
