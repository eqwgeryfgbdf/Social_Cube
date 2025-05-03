@echo off
REM Social Cube Deployment Script for Windows
REM This script assists with deploying the Social Cube application using Docker

REM Colors for output
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set NC=[0m

REM Function to print colored output
:print_message
    echo %~1%~2%NC%
    goto :eof

REM Check if Docker is installed
docker --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :print_message %RED% "Docker is not installed. Please install Docker first."
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :print_message %RED% "Docker Compose is not installed. Please install Docker Compose first."
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    call :print_message %YELLOW% "No .env file found. Creating from example..."
    if exist docker.env.example (
        copy docker.env.example .env
        call :print_message %GREEN% ".env file created from example. Please edit it with your actual settings."
    ) else (
        call :print_message %RED% "No docker.env.example file found. Please create a .env file manually."
        exit /b 1
    )
)

REM Process commands
if "%1"=="build" (
    call :print_message %GREEN% "Building Docker images..."
    docker-compose build
    goto :eof
) else if "%1"=="up" (
    call :print_message %GREEN% "Starting containers..."
    docker-compose up -d
    call :print_message %GREEN% "Containers started. Access the application at http://localhost"
    goto :eof
) else if "%1"=="down" (
    call :print_message %YELLOW% "Stopping containers..."
    docker-compose down
    goto :eof
) else if "%1"=="logs" (
    call :print_message %GREEN% "Showing logs (press Ctrl+C to exit)..."
    docker-compose logs -f
    goto :eof
) else if "%1"=="migrate" (
    call :print_message %GREEN% "Running migrations..."
    docker-compose exec web python manage.py migrate
    goto :eof
) else if "%1"=="collectstatic" (
    call :print_message %GREEN% "Collecting static files..."
    docker-compose exec web python manage.py collectstatic --noinput
    goto :eof
) else if "%1"=="createsuperuser" (
    call :print_message %GREEN% "Creating superuser..."
    docker-compose exec web python manage.py createsuperuser
    goto :eof
) else if "%1"=="backup" (
    call :print_message %GREEN% "Backing up database..."
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set DATE=%%c%%a%%b)
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do (set TIME=%%a%%b)
    set TIMESTAMP=%DATE%_%TIME%
    if not exist backups mkdir backups
    docker-compose exec db pg_dump -U postgres social_cube > backups\backup_%TIMESTAMP%.sql
    call :print_message %GREEN% "Backup created: backups\backup_%TIMESTAMP%.sql"
    goto :eof
) else if "%1"=="restore" (
    if "%2"=="" (
        call :print_message %RED% "No backup file specified. Usage: deploy.bat restore FILE"
        exit /b 1
    )
    
    if not exist "%2" (
        call :print_message %RED% "Backup file not found: %2"
        exit /b 1
    )
    
    call :print_message %YELLOW% "WARNING: This will overwrite the current database. Continue? [y/N]"
    set /p confirm=""
    if /i "%confirm%"=="y" (
        call :print_message %GREEN% "Restoring database from %2..."
        type "%2" | docker-compose exec -T db psql -U postgres social_cube
        call :print_message %GREEN% "Database restored."
    ) else (
        call :print_message %YELLOW% "Database restore canceled."
    )
    goto :eof
) else (
    call :show_help
    goto :eof
)

:show_help
    echo Social Cube Deployment Script for Windows
    echo.
    echo Usage: deploy.bat [OPTION]
    echo.
    echo Options:
    echo   build           Build the Docker images
    echo   up              Start the containers
    echo   down            Stop the containers
    echo   logs            Show logs
    echo   migrate         Run database migrations
    echo   collectstatic   Collect static files
    echo   createsuperuser Create a superuser
    echo   backup          Backup the database
    echo   restore FILE    Restore the database from a backup file
    echo   help            Show this help message
    echo.
    goto :eof