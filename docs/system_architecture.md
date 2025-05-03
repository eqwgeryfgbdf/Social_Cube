# System Architecture

This document provides an overview of the Social Cube system architecture, explaining how the different components interact with each other.

## Architecture Overview

Social Cube is built on a modular architecture consisting of several key components:

![Social Cube Architecture](../static/img/docs/architecture_diagram.png)

## Core Components

### 1. Web Application (Django)

The main Django application serves as the core of the system, handling HTTP requests, rendering templates, and interfacing with the database.

**Key Components**:
- **Views**: Handle HTTP requests and return responses
- **Models**: Define the database schema and business logic
- **Templates**: Define the presentation layer
- **URLs**: Define the routing for HTTP requests
- **Middleware**: Process requests/responses globally
- **Forms**: Handle form validation and processing

### 2. API Layer (Django REST Framework)

The API layer provides a RESTful interface for frontend and bot communication. It handles authentication, serialization, and validation.

**Key Components**:
- **Serializers**: Convert complex data types to Python primitives and vice versa
- **ViewSets**: Handle API requests and responses
- **Routers**: Define the routing for API endpoints
- **Throttling**: Implement rate limiting
- **Permissions**: Define access control rules

### 3. Bot Management System

The Bot Management System is responsible for managing Discord bots, including creation, configuration, and monitoring.

**Key Components**:
- **Bot Manager**: Singleton service that manages bot instances
- **Bot Client**: Individual bot instance that connects to Discord
- **Command Registry**: Registers and manages bot commands
- **Event Handlers**: Handle Discord events
- **Synchronization**: Sync commands and server information with Discord

### 4. Real-time System (Django Channels)

The real-time system provides WebSocket connections for real-time updates, using Django Channels and Redis as the backing store.

**Key Components**:
- **Consumers**: Handle WebSocket connections and messages
- **Channel Layers**: Manage message routing between different instances
- **Groups**: Manage groups of channels for broadcasting
- **Middleware**: Process WebSocket connections globally

### 5. Database Layer

The database layer stores all persistent data, using PostgreSQL in production or SQLite in development.

**Key Models**:
- **User**: Extended Django user model
- **Bot**: Bot configuration and credentials
- **Guild**: Discord server information
- **GuildSettings**: Server-specific settings
- **Command**: Bot command configuration
- **CommandOption**: Options for commands
- **CommandLog**: Logs of command usage
- **BotLog**: Logs of bot events
- **RequestLog**: Logs of HTTP requests
- **AuditLog**: Logs of user actions
- **ErrorLog**: Logs of application errors

### 6. Caching Layer (Redis)

Redis is used for caching, session storage, and as the backing store for Django Channels.

**Key Use Cases**:
- **Session Storage**: Store session data for authenticated users
- **Caching**: Cache frequently accessed data
- **Channels Backend**: Store channel layer data for WebSockets
- **Rate Limiting**: Implement rate limiting for API endpoints

### 7. Task Queue (Celery)

Celery is used for handling background tasks, scheduled tasks, and asynchronous operations.

**Key Use Cases**:
- **Scheduled Tasks**: Run tasks at specified intervals
- **Background Processing**: Handle long-running tasks asynchronously
- **Email Sending**: Send emails asynchronously
- **Data Processing**: Process data in the background

## Data Flow

### 1. User Authentication Flow

1. User visits the login page
2. User clicks "Login with Discord"
3. User is redirected to Discord OAuth2 authorization page
4. User authorizes the application
5. Discord redirects back to the application with an authorization code
6. The application exchanges the code for an access token
7. The application uses the access token to fetch user information from Discord
8. The application creates or updates the user record in the database
9. The application creates a session for the authenticated user
10. The user is redirected to the dashboard

### 2. Bot Creation Flow

1. User visits the bot creation page
2. User enters bot information (name, description, token)
3. The application creates a new bot record in the database
4. The Bot Manager service creates a new bot instance
5. The bot connects to Discord
6. The bot fetches initial information from Discord (guilds, channels, etc.)
7. The application syncs this information with the database
8. The user is redirected to the bot details page

### 3. Command Execution Flow

1. A Discord user types a command in a server
2. The bot receives the command event from Discord
3. The bot checks if the command exists and is active
4. The bot executes the command
5. The bot logs the command execution in the database
6. The bot responds to the user in Discord
7. The WebSocket server broadcasts the command log to connected clients
8. The dashboard updates in real-time to show the command execution

## Deployment Architecture

In production, Social Cube is deployed using Docker Compose with the following services:

### Services

- **Web**: Django web application (Gunicorn)
- **ASGI**: Django Channels for WebSockets (Daphne)
- **DB**: PostgreSQL database
- **Redis**: Redis for caching and channels
- **Nginx**: Web server for handling HTTP requests and serving static files
- **Certbot**: SSL certificate management

### Service Dependencies

```
├── Web
│   ├── DB
│   └── Redis
├── ASGI
│   ├── DB
│   ├── Redis
│   └── Web
├── Nginx
│   └── Web
└── Certbot
    └── Nginx
```

## Database Schema

The database schema consists of the following key tables and their relationships:

![Database Schema](../static/img/docs/database_schema.png)

### Key Tables

- **auth_user**: Django's built-in user model
- **bot_management_bot**: Bot configuration and credentials
- **bot_management_guild**: Discord server information
- **bot_management_guildsettings**: Server-specific settings
- **bot_management_command**: Bot command configuration
- **bot_management_commandoption**: Options for commands
- **bot_management_commandlog**: Logs of command usage
- **bot_management_botlog**: Logs of bot events
- **logging_system_requestlog**: Logs of HTTP requests
- **logging_system_auditlog**: Logs of user actions
- **logging_system_errorlog**: Logs of application errors

## Security Considerations

### 1. Authentication and Authorization

- **OAuth2**: Use Discord OAuth2 for authentication
- **API Keys**: Use API keys for bot-to-server communication
- **Permission System**: Implement a fine-grained permission system for controlling access to resources
- **CSRF Protection**: Implement CSRF protection for all forms
- **Session Security**: Configure secure session settings (HTTPS only, HTTP only, etc.)

### 2. Data Security

- **Environment Variables**: Store sensitive information in environment variables
- **Database Security**: Implement database security best practices (strong passwords, limited access, etc.)
- **TLS/SSL**: Use TLS/SSL for all connections
- **Rate Limiting**: Implement rate limiting for API endpoints
- **Input Validation**: Validate all user input

### 3. Infrastructure Security

- **Docker**: Use Docker Compose for deployment
- **Firewall**: Configure firewall rules to restrict access
- **Regular Updates**: Keep all dependencies up to date
- **Monitoring**: Implement monitoring and alerting
- **Backup**: Regularly backup all data

## Performance Optimizations

### 1. Caching

- **Redis Cache**: Cache frequently accessed data using Redis
- **Template Caching**: Cache rendered templates
- **Database Query Caching**: Cache database queries

### 2. Database Optimizations

- **Indexing**: Create appropriate indexes for frequently queried fields
- **Connection Pooling**: Implement connection pooling for database connections
- **Query Optimization**: Optimize database queries

### 3. Scaling Considerations

- **Horizontal Scaling**: Ability to scale web and ASGI services horizontally
- **Load Balancing**: Use Nginx as a load balancer
- **Database Scaling**: Consider using database replication or sharding for high load scenarios

## Monitoring and Logging

### 1. Logging

- **Application Logs**: Log application events to files and console
- **Error Logs**: Log application errors to database and files
- **Access Logs**: Log HTTP requests to database and files
- **Audit Logs**: Log user actions for security auditing

### 2. Monitoring

- **Health Check**: Implement a health check endpoint for monitoring
- **Metrics**: Collect metrics on application performance
- **Alerts**: Configure alerts for critical events

## Extension Points

The system is designed to be extensible in the following ways:

### 1. Bot Adapters

The Bot Management System uses an adapter pattern, allowing for integration with different bot frameworks or platforms.

### 2. Custom Commands

The Command System is extensible, allowing users to create custom commands with various options.

### 3. API Extensions

The API is versioned and designed for extension, allowing for new endpoints to be added without breaking existing clients.

### 4. Plugin System

A plugin system allows for extending the functionality of the application without modifying the core codebase.

## Conclusion

The Social Cube architecture is designed to be modular, scalable, and secure, allowing for easy extension and maintenance. The use of industry-standard technologies and patterns ensures a robust and reliable system.