#!/bin/bash

# Social Cube Deployment Script
# This script assists with deploying the Social Cube application using Docker

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_message "$RED" "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_message "$RED" "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_message "$YELLOW" "No .env file found. Creating from example..."
    if [ -f docker.env.example ]; then
        cp docker.env.example .env
        print_message "$GREEN" ".env file created from example. Please edit it with your actual settings."
    else
        print_message "$RED" "No docker.env.example file found. Please create a .env file manually."
        exit 1
    fi
fi

# Function to display help
show_help() {
    echo "Social Cube Deployment Script"
    echo ""
    echo "Usage: ./deploy.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  build           Build the Docker images"
    echo "  up              Start the containers"
    echo "  down            Stop the containers"
    echo "  logs            Show logs"
    echo "  migrate         Run database migrations"
    echo "  collectstatic   Collect static files"
    echo "  createsuperuser Create a superuser"
    echo "  backup          Backup the database"
    echo "  restore FILE    Restore the database from a backup file"
    echo "  help            Show this help message"
    echo ""
}

# Process commands
case "$1" in
    build)
        print_message "$GREEN" "Building Docker images..."
        docker-compose build
        ;;
    up)
        print_message "$GREEN" "Starting containers..."
        docker-compose up -d
        print_message "$GREEN" "Containers started. Access the application at http://localhost"
        ;;
    down)
        print_message "$YELLOW" "Stopping containers..."
        docker-compose down
        ;;
    logs)
        print_message "$GREEN" "Showing logs (press Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    migrate)
        print_message "$GREEN" "Running migrations..."
        docker-compose exec web python manage.py migrate
        ;;
    collectstatic)
        print_message "$GREEN" "Collecting static files..."
        docker-compose exec web python manage.py collectstatic --noinput
        ;;
    createsuperuser)
        print_message "$GREEN" "Creating superuser..."
        docker-compose exec web python manage.py createsuperuser
        ;;
    backup)
        print_message "$GREEN" "Backing up database..."
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        mkdir -p backups
        docker-compose exec db pg_dump -U postgres social_cube > backups/backup_${TIMESTAMP}.sql
        print_message "$GREEN" "Backup created: backups/backup_${TIMESTAMP}.sql"
        ;;
    restore)
        if [ -z "$2" ]; then
            print_message "$RED" "No backup file specified. Usage: ./deploy.sh restore FILE"
            exit 1
        fi
        
        if [ ! -f "$2" ]; then
            print_message "$RED" "Backup file not found: $2"
            exit 1
        fi
        
        print_message "$YELLOW" "WARNING: This will overwrite the current database. Continue? [y/N]"
        read -r confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            print_message "$GREEN" "Restoring database from $2..."
            docker-compose exec -T db psql -U postgres social_cube < "$2"
            print_message "$GREEN" "Database restored."
        else
            print_message "$YELLOW" "Database restore canceled."
        fi
        ;;
    help|*)
        show_help
        ;;
esac