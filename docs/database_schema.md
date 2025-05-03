# Database Schema

This document provides a detailed description of the Social Cube database schema, including tables, fields, relationships, and indexes.

## Overview

Social Cube uses a relational database (PostgreSQL in production, SQLite in development) to store all persistent data. The schema is designed to support the following core entities:

- Users
- Bots
- Guilds (Discord servers)
- Commands
- Logs (bot events, command execution, errors)

## Core Tables

### Users

The user system extends Django's built-in user model.

#### `auth_user`

Django's built-in user table.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| password | String | Hashed password |
| last_login | DateTime | Last login timestamp |
| is_superuser | Boolean | Superuser status |
| username | String | Unique username |
| first_name | String | User's first name |
| last_name | String | User's last name |
| email | String | User's email address |
| is_staff | Boolean | Staff status |
| is_active | Boolean | Active status |
| date_joined | DateTime | Registration timestamp |

#### `dashboard_userprofile`

Extends the built-in user model with Discord-specific information.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to auth_user |
| discord_id | String | Discord user ID |
| discord_username | String | Discord username |
| discord_avatar | String | Discord avatar URL |
| discord_discriminator | String | Discord discriminator |
| discord_access_token | String | Discord OAuth2 access token |
| discord_refresh_token | String | Discord OAuth2 refresh token |
| discord_token_expires | DateTime | Token expiration timestamp |
| preferences | JSON | User preferences |

### Bot Management

#### `bot_management_bot`

Stores information about Discord bots managed by the application.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Bot name |
| description | Text | Bot description |
| token | String | Discord bot token (encrypted) |
| client_id | String | Discord application client ID |
| application_id | String | Discord application ID |
| owner_id | Integer | Foreign key to auth_user |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| last_active | DateTime | Last active timestamp |
| status | String | Bot status (active, inactive, error) |
| is_public | Boolean | Whether the bot is public |
| avatar | String | Bot avatar URL |

**Indexes**:
- `bot_management_bot_owner_id_idx`: Index on owner_id
- `bot_management_bot_status_idx`: Index on status
- `bot_management_bot_created_at_idx`: Index on created_at

#### `bot_management_botlog`

Logs events related to bot operation.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| bot_id | Integer | Foreign key to bot_management_bot |
| event_type | String | Type of event |
| description | Text | Event description |
| timestamp | DateTime | Event timestamp |
| details | JSON | Additional event details |

**Indexes**:
- `bot_management_botlog_bot_id_idx`: Index on bot_id
- `bot_management_botlog_timestamp_idx`: Index on timestamp
- `bot_management_botlog_event_type_idx`: Index on event_type

### Guild Management

#### `bot_management_guild`

Stores information about Discord servers (guilds) where bots are installed.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| bot_id | Integer | Foreign key to bot_management_bot |
| guild_id | String | Discord guild ID |
| name | String | Guild name |
| icon | String | Guild icon URL |
| owner_id | String | Discord user ID of guild owner |
| member_count | Integer | Number of members in the guild |
| created_at | DateTime | Creation timestamp |
| joined_at | DateTime | Bot join timestamp |
| last_synced | DateTime | Last sync timestamp |
| is_active | Boolean | Whether the bot is active in this guild |

**Indexes**:
- `bot_management_guild_bot_id_idx`: Index on bot_id
- `bot_management_guild_guild_id_idx`: Index on guild_id
- `bot_management_guild_is_active_idx`: Index on is_active

#### `bot_management_guildsettings`

Stores guild-specific settings.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| guild_id | Integer | Foreign key to bot_management_guild |
| prefix | String | Command prefix for this guild |
| notification_channel_id | String | Discord channel ID for notifications |
| welcome_message | Text | Welcome message for new members |
| farewell_message | Text | Farewell message for leaving members |
| enable_welcome | Boolean | Whether to enable welcome messages |
| enable_farewell | Boolean | Whether to enable farewell messages |
| log_channel_id | String | Discord channel ID for logging |
| mod_role_id | String | Discord role ID for moderators |
| admin_role_id | String | Discord role ID for administrators |
| premium_status | String | Premium status of this guild |
| custom_settings | JSON | Additional custom settings |

**Indexes**:
- `bot_management_guildsettings_guild_id_idx`: Index on guild_id

#### `bot_management_guildchannel`

Stores information about Discord channels in guilds.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| guild_id | Integer | Foreign key to bot_management_guild |
| channel_id | String | Discord channel ID |
| name | String | Channel name |
| type | String | Channel type (text, voice, category) |
| position | Integer | Channel position |
| parent_id | String | Parent category ID |
| is_nsfw | Boolean | Whether the channel is NSFW |
| last_synced | DateTime | Last sync timestamp |

**Indexes**:
- `bot_management_guildchannel_guild_id_idx`: Index on guild_id
- `bot_management_guildchannel_channel_id_idx`: Index on channel_id

### Command Management

#### `bot_management_command`

Stores information about Discord slash commands.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| bot_id | Integer | Foreign key to bot_management_bot |
| guild_id | Integer | Foreign key to bot_management_guild (null for global commands) |
| name | String | Command name |
| description | Text | Command description |
| type | String | Command type (chat_input, user, message) |
| is_active | Boolean | Whether the command is active |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |
| last_synced | DateTime | Last sync timestamp |
| permissions | JSON | Permission configuration |
| discord_id | String | Discord command ID |

**Indexes**:
- `bot_management_command_bot_id_idx`: Index on bot_id
- `bot_management_command_guild_id_idx`: Index on guild_id
- `bot_management_command_is_active_idx`: Index on is_active

#### `bot_management_commandoption`

Stores options for commands.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| command_id | Integer | Foreign key to bot_management_command |
| name | String | Option name |
| description | Text | Option description |
| type | String | Option type (string, integer, boolean, user, etc.) |
| is_required | Boolean | Whether the option is required |
| position | Integer | Option position |
| choices | JSON | Available choices for the option |
| min_value | Float | Minimum value (for number types) |
| max_value | Float | Maximum value (for number types) |
| min_length | Integer | Minimum length (for string types) |
| max_length | Integer | Maximum length (for string types) |

**Indexes**:
- `bot_management_commandoption_command_id_idx`: Index on command_id

#### `bot_management_commandlog`

Logs command executions.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| command_id | Integer | Foreign key to bot_management_command |
| guild_id | String | Discord guild ID |
| channel_id | String | Discord channel ID |
| user_id | String | Discord user ID |
| timestamp | DateTime | Execution timestamp |
| status | String | Execution status (success, error) |
| error_message | Text | Error message (if status is error) |
| parameters | JSON | Command parameters |
| execution_time | Float | Execution time in seconds |

**Indexes**:
- `bot_management_commandlog_command_id_idx`: Index on command_id
- `bot_management_commandlog_timestamp_idx`: Index on timestamp
- `bot_management_commandlog_status_idx`: Index on status

### Logging System

#### `logging_system_requestlog`

Logs HTTP requests to the application.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| timestamp | DateTime | Request timestamp |
| method | String | HTTP method |
| path | String | Request path |
| status_code | Integer | HTTP status code |
| duration | Float | Request duration in seconds |
| user_id | Integer | Foreign key to auth_user (null for anonymous users) |
| ip_address | String | Client IP address |
| user_agent | String | Client user agent |
| request_data | JSON | Request data |
| response_data | JSON | Response data |

**Indexes**:
- `logging_system_requestlog_timestamp_idx`: Index on timestamp
- `logging_system_requestlog_status_code_idx`: Index on status_code
- `logging_system_requestlog_user_id_idx`: Index on user_id

#### `logging_system_auditlog`

Logs user actions for auditing purposes.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| timestamp | DateTime | Action timestamp |
| user_id | Integer | Foreign key to auth_user |
| action | String | Action type (create, update, delete, etc.) |
| entity_type | String | Entity type (bot, guild, command, etc.) |
| entity_id | String | Entity ID |
| description | Text | Action description |
| context | JSON | Additional context information |

**Indexes**:
- `logging_system_auditlog_timestamp_idx`: Index on timestamp
- `logging_system_auditlog_user_id_idx`: Index on user_id
- `logging_system_auditlog_action_idx`: Index on action
- `logging_system_auditlog_entity_type_idx`: Index on entity_type

#### `logging_system_errorlog`

Logs application errors.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| timestamp | DateTime | Error timestamp |
| level | String | Error level (debug, info, warning, error, critical) |
| message | Text | Error message |
| module | String | Module where the error occurred |
| function | String | Function where the error occurred |
| exception | Text | Exception details |
| stack_trace | Text | Stack trace |
| request_id | String | Related request ID |
| user_id | Integer | Foreign key to auth_user (null if not applicable) |
| context | JSON | Additional context information |

**Indexes**:
- `logging_system_errorlog_timestamp_idx`: Index on timestamp
- `logging_system_errorlog_level_idx`: Index on level
- `logging_system_errorlog_user_id_idx`: Index on user_id

## Relationships

### One-to-Many Relationships

- `auth_user` to `dashboard_userprofile`: One user has one profile
- `auth_user` to `bot_management_bot`: One user can own many bots
- `bot_management_bot` to `bot_management_guild`: One bot can be in many guilds
- `bot_management_bot` to `bot_management_botlog`: One bot can have many logs
- `bot_management_bot` to `bot_management_command`: One bot can have many commands
- `bot_management_guild` to `bot_management_guildsettings`: One guild has one settings record
- `bot_management_guild` to `bot_management_guildchannel`: One guild can have many channels
- `bot_management_command` to `bot_management_commandoption`: One command can have many options
- `bot_management_command` to `bot_management_commandlog`: One command can have many logs

### Many-to-Many Relationships

- `auth_user` to `auth_group`: Users can belong to multiple groups (Django's built-in groups)
- `auth_user` to `auth_permission`: Users can have multiple permissions (Django's built-in permissions)

## Migrations

Database migrations are managed using Django's migration system. All migrations are stored in the `migrations` directory of each app.

## Backup and Restore

### Backup

To backup the database, use the provided backup script or the following command:

```bash
pg_dump -U <username> <database_name> > backup_$(date +%Y%m%d).sql
```

### Restore

To restore the database from a backup, use the following command:

```bash
cat backup_file.sql | psql -U <username> <database_name>
```

## Database Configuration

The database connection is configured using environment variables:

- `DATABASE_URL`: Database connection URL
- `DB_ENGINE`: Database engine
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_HOST`: Database host
- `DB_PORT`: Database port

## Performance Considerations

### Indexing

All frequently queried fields are indexed for optimal performance. Additional indexes may be added based on query patterns.

### Connection Pooling

Connection pooling is configured in production to minimize the overhead of establishing new database connections.

### Query Optimization

Complex queries are optimized using Django's QuerySet API to minimize database load.

## Data Integrity

### Constraints

- Foreign key constraints ensure referential integrity
- Unique constraints prevent duplicate records
- Not-null constraints ensure required fields are provided

### Transactions

Django's transaction management is used to ensure data integrity during complex operations.

## Security Considerations

### Database Access

Access to the database is restricted to the application and administrators.

### Sensitive Data

Sensitive data (like bot tokens) is encrypted before storage.

### Query Parameters

All queries use parameterized queries to prevent SQL injection attacks.