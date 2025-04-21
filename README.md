
# Django Application with MySQL in Docker: Setup and Troubleshooting Documentation

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Docker Configuration](#docker-configuration)
4. [Troubleshooting Steps](#troubleshooting-steps)
5. [Final Steps](#final-steps)

## Prerequisites
- Docker and Docker Compose installed on your machine.
- Python and Django installed locally for development.
- MySQL installed locally (if needed for initial testing).

## Initial Setup
1. **Create a Django Project**:
   ```bash
   django-admin startproject your_project_name
   cd your_project_name
   ```

2. **Create a Virtual Environment** (optional for local development):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Required Packages**:
   ```bash
   pip install django mysqlclient
   ```

## Docker Configuration
1. **Create a `Dockerfile`** in your project directory:
   ```dockerfile
   FROM python:3.12

   WORKDIR /app

   COPY requirements.txt .

   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
   ```

2. **Create a `docker-compose.yml`** file:
   ```yaml
   version: '3.8'

   services:
     db:
       image: mysql:latest
       environment:
         MYSQL_DATABASE: your_database_name
         MYSQL_ROOT_PASSWORD: Kamal1395
       ports:
         - "3306:3306"
       volumes:
         - db_data:/var/lib/mysql

     web:
       build: .
       command: python manage.py runserver 0.0.0.0:8000
       ports:
         - "8000:8000"
       volumes:
         - .:/app
       depends_on:
         - db
       environment:
         - DATABASE_URL=mysql://root:Kamal1395@db:3306/your_database_name

   volumes:
     db_data:
   ```

## Troubleshooting Steps

### Issue 1: MySQL Connection Errors
- **Error**: `django.db.utils.OperationalError: (2002, "Can't connect to local server through socket...")`
- **Solution**:
  1. Ensure MySQL is running locally.
  2. Check the database configuration in `settings.py`.
  3. Use `127.0.0.1` instead of `localhost` in the configuration.

### Issue 2: MySQL Plugin Not Loaded
- **Error**: `ERROR 1524 (HY000): Plugin 'mysql_native_password' is not loaded`
- **Solution**:
  1. Log in to MySQL and enable the plugin:
     ```sql
     INSTALL PLUGIN mysql_native_password SONAME 'mysql_native_password.so';
     ```
  2. Change the user authentication method:
     ```sql
     ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
     ```

### Issue 3: Port Conflicts
- **Error**: `Error response from daemon: Ports are not available...`
- **Solution**:
  1. Check if another service is using port `3306`:
     ```bash
     netstat -ano | findstr :3306
     ```
  2. Stop the conflicting service or change the port mapping in `docker-compose.yml`.

### Issue 4: MySQL User Configuration
- **Error**: `MYSQL_USER="root", MYSQL_USER and MYSQL_PASSWORD are for configuring a regular user...`
- **Solution**:
  1. Remove the `MYSQL_USER` environment variable from the `docker-compose.yml` file.

## Final Steps
1. **Build and Start Docker Containers**:
   ```bash
   docker-compose up -d --build
   ```

2. **Run Migrations**:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Access the Application**:
   - Open a web browser and navigate to `http://localhost:8000`.

4. **Create a Superuser** (optional):
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Stop the Containers**:
   ```bash
   docker-compose down
   ```

---

This documentation summarizes the steps taken to set up your Django application with MySQL in Docker, along with troubleshooting steps for common issues encountered during the process. 
