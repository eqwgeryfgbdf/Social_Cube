# API Reference

This document provides comprehensive information about the Social Cube API endpoints, request/response formats, and error handling.

## Authentication

All API requests require authentication except for the health check endpoint. The API supports two authentication methods:

### OAuth2 Token (Recommended)

Include an OAuth2 bearer token in the Authorization header:

```
Authorization: Bearer <token>
```

OAuth2 tokens can be obtained through the Discord OAuth2 flow.

### API Key (For Bot Access)

For bot-to-server communication, include an API key in the header:

```
X-API-Key: <api_key>
```

API keys can be generated in the bot settings page.

## API Endpoints

### Health Check

**Endpoint**: `GET /health/`

**Description**: Check the health status of the application.

**Authentication**: None required

**Response**:

```json
{
  "status": "ok",
  "components": {
    "database": true,
    "redis": true,
    "application": true
  },
  "errors": []
}
```

### Bot Management

#### List Bots

**Endpoint**: `GET /api/bots/`

**Description**: Retrieve a list of bots owned by the authenticated user.

**Query Parameters**:
- `page`: Page number for pagination (default: 1)
- `limit`: Number of items per page (default: 10)
- `status`: Filter by bot status (e.g., "active", "inactive")

**Response**:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "ModerationBot",
      "description": "A bot for server moderation",
      "status": "active",
      "created_at": "2025-04-15T12:00:00Z",
      "last_active": "2025-04-27T10:30:00Z"
    },
    {
      "id": 2,
      "name": "WelcomeBot",
      "description": "A bot for welcoming new members",
      "status": "inactive",
      "created_at": "2025-04-20T14:30:00Z",
      "last_active": null
    }
  ]
}
```

#### Get Bot Details

**Endpoint**: `GET /api/bots/{bot_id}/`

**Description**: Retrieve detailed information about a specific bot.

**Response**:

```json
{
  "id": 1,
  "name": "ModerationBot",
  "description": "A bot for server moderation",
  "status": "active",
  "created_at": "2025-04-15T12:00:00Z",
  "last_active": "2025-04-27T10:30:00Z",
  "avatar_url": "https://cdn.discordapp.com/avatars/123456789/abcdef123456.png",
  "owner": {
    "id": 1,
    "username": "admin"
  },
  "guilds_count": 5,
  "commands_count": 10
}
```

#### Create Bot

**Endpoint**: `POST /api/bots/`

**Description**: Create a new Discord bot.

**Request Body**:

```json
{
  "name": "MusicBot",
  "description": "A bot for playing music in Discord servers",
  "token": "your_discord_bot_token"
}
```

**Response**: Returns the created bot object with status code 201.

#### Update Bot

**Endpoint**: `PUT /api/bots/{bot_id}/`

**Description**: Update an existing bot's information.

**Request Body**:

```json
{
  "name": "MusicBot Pro",
  "description": "An enhanced bot for playing music in Discord servers"
}
```

**Response**: Returns the updated bot object.

### Guild Management

#### List Guilds

**Endpoint**: `GET /api/bots/{bot_id}/guilds/`

**Description**: Retrieve a list of guilds (servers) where the bot is installed.

**Query Parameters**:
- `page`: Page number for pagination (default: 1)
- `limit`: Number of items per page (default: 10)
- `search`: Search by guild name

**Response**:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "123456789012345678",
      "name": "Gaming Community",
      "icon": "https://cdn.discordapp.com/icons/123456789012345678/abcdef123456.png",
      "member_count": 250,
      "joined_at": "2025-04-15T12:30:00Z"
    },
    {
      "id": "876543210987654321",
      "name": "Study Group",
      "icon": "https://cdn.discordapp.com/icons/876543210987654321/fedcba654321.png",
      "member_count": 50,
      "joined_at": "2025-04-20T14:45:00Z"
    }
  ]
}
```

### Command Management

#### List Commands

**Endpoint**: `GET /api/bots/{bot_id}/commands/`

**Description**: Retrieve a list of commands configured for the bot.

**Response**:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "ban",
      "description": "Ban a user from the server",
      "type": "chat_input",
      "is_active": true,
      "created_at": "2025-04-15T12:35:00Z",
      "last_synced": "2025-04-27T10:30:00Z"
    },
    {
      "id": 2,
      "name": "kick",
      "description": "Kick a user from the server",
      "type": "chat_input",
      "is_active": true,
      "created_at": "2025-04-15T12:36:00Z",
      "last_synced": "2025-04-27T10:30:00Z"
    }
  ]
}
```

#### Create Command

**Endpoint**: `POST /api/bots/{bot_id}/commands/`

**Description**: Create a new command for the bot.

**Request Body**:

```json
{
  "name": "mute",
  "description": "Mute a user in the server",
  "type": "chat_input",
  "guild_id": "123456789012345678",  // Optional, for guild-specific commands
  "options": [
    {
      "name": "user",
      "description": "The user to mute",
      "type": "user",
      "required": true
    },
    {
      "name": "duration",
      "description": "Duration in minutes",
      "type": "integer",
      "required": false
    }
  ]
}
```

**Response**: Returns the created command object with status code 201.

### Command Logs

#### List Command Logs

**Endpoint**: `GET /api/bots/{bot_id}/commands/{command_id}/logs/`

**Description**: Retrieve logs of command usage.

**Query Parameters**:
- `page`: Page number for pagination (default: 1)
- `limit`: Number of items per page (default: 10)
- `guild_id`: Filter by guild ID
- `user_id`: Filter by user ID
- `start_date`: Filter by start date (ISO format)
- `end_date`: Filter by end date (ISO format)

**Response**:

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "command_id": 1,
      "command_name": "ban",
      "guild_id": "123456789012345678",
      "guild_name": "Gaming Community",
      "user_id": "111222333444555666",
      "username": "User#1234",
      "timestamp": "2025-04-27T12:35:00Z",
      "status": "success"
    },
    {
      "id": 2,
      "command_id": 1,
      "command_name": "ban",
      "guild_id": "123456789012345678",
      "guild_name": "Gaming Community",
      "user_id": "222333444555666777",
      "username": "User#5678",
      "timestamp": "2025-04-27T14:20:00Z",
      "status": "error",
      "error_message": "Missing permissions"
    }
  ]
}
```

## WebSocket API

The Social Cube application also provides WebSocket endpoints for real-time updates.

### Connection

Connect to the WebSocket server using the following URL:

```
wss://yourdomain.com/ws/<endpoint>/
```

### Available WebSocket Endpoints

#### Bot Status Updates

**Endpoint**: `/ws/bot-status/<bot_id>/`

**Description**: Receive real-time updates about bot status changes.

**Example Message**:

```json
{
  "type": "bot_status_update",
  "data": {
    "bot_id": 1,
    "status": "online",
    "timestamp": "2025-04-27T15:30:00Z"
  }
}
```

#### Guild Activity

**Endpoint**: `/ws/guild-activity/<bot_id>/<guild_id>/`

**Description**: Receive real-time updates about guild events.

**Example Message**:

```json
{
  "type": "guild_activity",
  "data": {
    "bot_id": 1,
    "guild_id": "123456789012345678",
    "event_type": "member_join",
    "user_id": "333444555666777888",
    "timestamp": "2025-04-27T15:35:00Z"
  }
}
```

#### Command Logs

**Endpoint**: `/ws/command-logs/<bot_id>/`

**Description**: Receive real-time updates about command usage.

**Example Message**:

```json
{
  "type": "command_log",
  "data": {
    "bot_id": 1,
    "command_id": 2,
    "command_name": "kick",
    "guild_id": "123456789012345678",
    "user_id": "444555666777888999",
    "status": "success",
    "timestamp": "2025-04-27T15:40:00Z"
  }
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of an API request.

### Common Status Codes

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Error Response Format

```json
{
  "error": {
    "code": "resource_not_found",
    "message": "The requested resource was not found",
    "details": {
      "resource_type": "Bot",
      "resource_id": "999"
    }
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse. Rate limits are applied per user/API key.

- Rate limit headers are included in API responses:
  - `X-RateLimit-Limit`: Number of allowed requests in the current period
  - `X-RateLimit-Remaining`: Number of remaining requests in the current period
  - `X-RateLimit-Reset`: Time in seconds until the rate limit resets

When rate limited, the API returns a `429 Too Many Requests` status code.

## Pagination

List endpoints support pagination with the following query parameters:

- `page`: Page number (starting from 1)
- `limit`: Number of items per page (default: 10, max: 100)

Pagination information is included in the response:

```json
{
  "count": 42,  // Total number of items
  "next": "https://api.yourdomain.com/api/bots/?page=2&limit=10",  // URL to next page
  "previous": null,  // URL to previous page
  "results": [...]  // List of items for the current page
}
```