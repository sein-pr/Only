# Deployment Guide for Shopy Flask Application

## Important Note About Netlify Deployment

⚠️ **Flask applications cannot be directly deployed to Netlify.** Netlify is designed to serve static websites and frontend applications only. Flask is a backend framework that requires a server to run, which Netlify does not provide.

## Recommended Hosting Platforms

Choose one of the following platforms to deploy your Flask application:

### 1. Heroku (Recommended for beginners)
- Create a free account at heroku.com
- Install Heroku CLI
- Create the following files in your project root:
  - `requirements.txt` (already created)
  - `runtime.txt` (already created with Python version)
  - `Procfile` (already created)
- Deploy using Heroku CLI

### 2. Railway
- Sign up at railway.app
- Connect your GitHub repository
- Railway automatically detects and deploys Python/Flask apps
- Works with SQLite (using persistent volumes)

### 3. PythonAnywhere
- Create an account at pythonanywhere.com
- Upload your code via Git or direct file upload
- Configure a web app with your Flask application
- Note: SQLite works well on PythonAnywhere

### 4. AWS Elastic Beanstalk
- More advanced option
- Good scalability
- May require RDS for production databases instead of SQLite

### 5. Google Cloud Platform (App Engine)
- Good for Google ecosystem users
- Requires some configuration for SQLite

## Deployment Steps (Heroku Example)

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create a Heroku app**
   ```bash
   heroku create your-app-name
   ```

4. **Deploy your application**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push heroku main
   ```

5. **Open your application**
   ```bash
   heroku open
   ```

## Configuration Files Included

The following files have been prepared for deployment:

- `requirements.txt` - Contains all Python dependencies
- `runtime.txt` - Specifies Python version (3.11.5)
- `Procfile` - Tells Heroku how to run your app
- `netlify.toml` - Documentation-only configuration for Netlify

## Database Considerations

Since you've switched to SQLite:
- SQLite works well for development and small-scale deployments
- For production, consider PostgreSQL or MySQL for better concurrency
- Some platforms (like Heroku) have ephemeral file systems - consider this for production

## Environment Variables

Set these environment variables on your hosting platform:

```
SECRET_KEY=your-production-secret-key
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
```

## Alternative: Split Frontend/Backend Architecture

If you want to use Netlify for the frontend:
1. Host the Flask API separately (Heroku/Railway)
2. Build your frontend as a separate React/Vue/Angular app
3. Deploy the frontend to Netlify
4. Configure API calls to your backend server

## Docker Deployment

The project also includes Docker configurations:
- `Dockerfile` - For containerized deployment
- `docker-compose.yml` - For local development
- `Dockerfile.prod` and `docker-compose.prod.yml` - For production

You can use these with platforms that support Docker containers.