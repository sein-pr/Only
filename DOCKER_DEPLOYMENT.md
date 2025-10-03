# Docker Deployment Guide for Shopy

This guide will help you deploy the Shopy application using Docker anywhere.

## Prerequisites

- Docker installed on your system
- Docker Compose installed
- Git (to clone the repository)

## Step-by-Step Deployment Instructions

### 1. Prepare Your Environment

#### Option A: Using the provided files
If you already have the Docker files in your project:

```bash
# Navigate to your project directory
cd /path/to/your/shopy/project
```

#### Option B: Clone from repository
```bash
# Clone your repository
git clone <your-repository-url>
cd shopy
```

### 2. Configure Environment Variables

1. **Copy the environment template:**
   ```bash
   cp env.example .env
   ```

2. **Edit the `.env` file with your actual values:**
   ```bash
   nano .env  # or use your preferred editor
   ```

   **Required configurations:**
   ```env
   # Flask Configuration
   SECRET_KEY=your-super-secret-key-change-this-in-production
   FLASK_ENV=production
   
   # Database Configuration (for Docker)
   DATABASE_URL=postgresql://postgres:password@db:5432/only_db
   
   # Email Configuration
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   
   # Stripe Configuration
   STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
   STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key
   ```

### 3. Build and Run with Docker Compose

#### For Development:
```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

#### For Production:
```bash
# Use the production Dockerfile
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

### 4. Initialize the Database

After the containers are running, you need to initialize the database:

```bash
# Run the migration script
docker-compose exec web python migrate_product_status.py

# Or if you need to create tables
docker-compose exec web python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database initialized!')
"
```

### 5. Access Your Application

- **Application:** http://localhost:5000
- **With Nginx:** http://localhost:80
- **Database:** localhost:5432 (PostgreSQL)
- **Redis:** localhost:6379 (if using)

### 6. Useful Docker Commands

#### View running containers:
```bash
docker-compose ps
```

#### View logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs db
```

#### Stop services:
```bash
docker-compose down
```

#### Stop and remove volumes (WARNING: This will delete your database):
```bash
docker-compose down -v
```

#### Rebuild after code changes:
```bash
docker-compose up --build
```

#### Execute commands in running container:
```bash
# Access the web container shell
docker-compose exec web bash

# Run Python commands
docker-compose exec web python -c "print('Hello from container!')"
```

### 7. Production Deployment

#### Using Docker Swarm:
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml shopy
```

#### Using Docker Compose with production settings:
```bash
# Use production Dockerfile
docker-compose -f docker-compose.yml up --build
```

### 8. Environment-Specific Configurations

#### Development:
- Uses development Dockerfile
- Includes debug tools
- Hot reloading enabled

#### Production:
- Uses production Dockerfile with gunicorn
- Optimized for performance
- Security hardened

### 9. Troubleshooting

#### Common Issues:

1. **Port already in use:**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :5000
   
   # Kill the process or change port in docker-compose.yml
   ```

2. **Database connection issues:**
   ```bash
   # Check if database is running
   docker-compose ps db
   
   # Check database logs
   docker-compose logs db
   ```

3. **Permission issues with uploads:**
   ```bash
   # Fix permissions
   docker-compose exec web chown -R appuser:appuser /app/static/uploads
   ```

4. **Out of memory:**
   ```bash
   # Clean up Docker
   docker system prune -a
   docker volume prune
   ```

### 10. Monitoring and Maintenance

#### Health Checks:
```bash
# Check application health
curl http://localhost:5000/

# Check database
docker-compose exec db pg_isready -U postgres
```

#### Backup Database:
```bash
# Create backup
docker-compose exec db pg_dump -U postgres only_db > backup.sql

# Restore backup
docker-compose exec -T db psql -U postgres only_db < backup.sql
```

#### Update Application:
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up --build -d
```

### 11. Scaling

#### Scale web service:
```bash
docker-compose up --scale web=3
```

#### Use load balancer:
```bash
# Add to docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - web
```

### 12. Security Considerations

1. **Change default passwords**
2. **Use environment variables for secrets**
3. **Enable HTTPS in production**
4. **Regular security updates**
5. **Database encryption**
6. **Network isolation**

## File Structure

```
shopy/
├── Dockerfile              # Development Dockerfile
├── Dockerfile.prod         # Production Dockerfile
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore          # Files to ignore in Docker build
├── env.example            # Environment variables template
├── nginx.conf             # Nginx configuration
├── requirements.txt       # Python dependencies
└── DOCKER_DEPLOYMENT.md   # This guide
```

## Support

If you encounter any issues:

1. Check the logs: `docker-compose logs`
2. Verify environment variables
3. Ensure all required services are running
4. Check network connectivity between containers

## Next Steps

After successful deployment:

1. Set up SSL certificates for HTTPS
2. Configure domain name
3. Set up monitoring and logging
4. Implement backup strategies
5. Configure CI/CD pipeline

