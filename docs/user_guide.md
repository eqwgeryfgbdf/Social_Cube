# User Guide

Welcome to Social Cube, a comprehensive Discord bot management platform. This guide will help you navigate the system and make the most of its features.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Bot Management](#bot-management)
4. [Guild (Server) Management](#guild-server-management)
5. [Command Management](#command-management)
6. [Statistics and Monitoring](#statistics-and-monitoring)
7. [Account Management](#account-management)
8. [Troubleshooting](#troubleshooting)
9. [Frequently Asked Questions](#frequently-asked-questions)

## Getting Started

### Account Creation

1. Visit the Social Cube website at `https://yourdomain.com`.
2. Click on **Login with Discord** to authenticate using your Discord account.
3. Authorize Social Cube to access your Discord information.
4. You will be redirected to the Social Cube dashboard after successful authentication.

### System Requirements

To use Social Cube, you need:

- A modern web browser (Chrome, Firefox, Safari, or Edge)
- A Discord account
- Internet connection

### First Login Experience

Upon your first login, you will:

1. Be greeted with a welcome tour highlighting key features.
2. Have the option to create your first bot.
3. View a sample dashboard with demo data to help you understand the platform.

## Dashboard Overview

The dashboard is your control center for managing all aspects of your Discord bots.

### Navigation

The main navigation menu includes:

- **Dashboard**: Overview of all your bots and their status.
- **Bots**: Detailed management of individual bots.
- **Servers**: Management of Discord servers where your bots are active.
- **Commands**: Configuration of bot commands.
- **Statistics**: Performance metrics and usage statistics.
- **Settings**: Account and application settings.

### Dashboard Widgets

The dashboard home page includes several widgets:

- **Bot Status**: Quick overview of all your bots and their current status.
- **Recent Activity**: Latest events from your bots.
- **Server Overview**: Summary of servers where your bots are active.
- **Command Usage**: Most frequently used commands.
- **System Health**: System status and notifications.

## Bot Management

### Creating a New Bot

1. Navigate to the **Bots** section.
2. Click the **Create New Bot** button.
3. Fill in the following information:
   - **Name**: Your bot's name.
   - **Description**: A brief description of your bot's purpose.
   - **Bot Token**: Your Discord bot token (see [Discord Developer Portal](https://discord.com/developers/applications) for instructions on creating a bot and obtaining a token).
4. Click **Create Bot**.

### Bot Settings

Each bot has various settings you can configure:

1. **Basic Information**:
   - Name
   - Description
   - Avatar (profile picture)
   - Status message

2. **Advanced Settings**:
   - Presence update interval
   - Command prefix (for text commands)
   - Default permissions
   - Auto-join new servers

To access these settings:
1. Go to the **Bots** section.
2. Click on the bot you want to configure.
3. Select the **Settings** tab.

### Bot Status

Bots can have the following statuses:

- **Online**: The bot is running and connected to Discord.
- **Offline**: The bot is not running.
- **Error**: The bot encountered an error and may not be functioning correctly.
- **Restarting**: The bot is currently restarting.

### Starting and Stopping Bots

To control your bot's operation:

1. Go to the **Bots** section.
2. Find the bot you want to control.
3. Use the **Start/Stop** toggle to change the bot's running state.

### Inviting a Bot to a Server

To add your bot to a Discord server:

1. Go to the **Bots** section.
2. Click on the bot you want to add to a server.
3. Click the **Invite to Server** button.
4. Select the server from the Discord authorization page.
5. Confirm the permissions.
6. The bot will join the selected server.

## Guild (Server) Management

### Server List

To view all servers where your bots are active:

1. Navigate to the **Servers** section.
2. You'll see a list of all servers with information including:
   - Server name
   - Member count
   - Bot name
   - Status
   - Last activity

### Server Details

To access detailed information about a server:

1. Go to the **Servers** section.
2. Click on a server name.

The server details page includes:

- **Overview**: General information about the server.
- **Channels**: List of text and voice channels.
- **Members**: List of server members.
- **Settings**: Server-specific bot settings.
- **Logs**: Recent bot activity in this server.

### Server Settings

Each server can have custom settings for your bot:

1. **Notification Settings**:
   - Welcome messages
   - Farewell messages
   - Notification channel

2. **Command Settings**:
   - Enabled/disabled commands
   - Command permissions
   - Command prefix (overrides bot default)

3. **Moderation Settings**:
   - Auto-moderation rules
   - Log channel
   - Moderator roles

To configure these settings:
1. Go to the **Servers** section.
2. Click on a server.
3. Select the **Settings** tab.

### Server Synchronization

To update server information from Discord:

1. Go to the **Servers** section.
2. Click on a server.
3. Click the **Sync with Discord** button.

This will update the following information:
- Channel list
- Role list
- Member count
- Server settings

## Command Management

### Command Types

Social Cube supports different types of Discord commands:

- **Slash Commands**: Commands that start with `/` and show options directly in Discord.
- **User Commands**: Commands that appear in the context menu when right-clicking a user.
- **Message Commands**: Commands that appear in the context menu when right-clicking a message.

### Creating Commands

To create a new command:

1. Navigate to the **Commands** section.
2. Click the **Create Command** button.
3. Fill in the command details:
   - **Name**: Command name (no spaces).
   - **Description**: Brief explanation of what the command does.
   - **Type**: Slash, User, or Message command.
   - **Options**: Parameters the command accepts (for slash commands).
   - **Permissions**: Who can use this command.
   - **Guild-specific**: Whether this command is for all servers or specific ones.
4. Click **Create Command**.

### Command Options

For slash commands, you can add options (parameters):

1. When creating or editing a command, scroll to the **Options** section.
2. Click **Add Option**.
3. Configure the option:
   - **Name**: Option name (no spaces).
   - **Description**: What this option is for.
   - **Type**: String, Integer, Boolean, User, Channel, Role, etc.
   - **Required**: Whether this option is mandatory.
   - **Choices**: Pre-defined choices for the option (if applicable).
4. Add additional options as needed.

### Command Permissions

To set permissions for a command:

1. When creating or editing a command, go to the **Permissions** section.
2. Choose from:
   - **Everyone**: Any user can use the command.
   - **Admin Only**: Only server administrators can use the command.
   - **Custom Roles**: Specific roles that can use the command.
3. For custom roles, you can configure different roles for each server.

### Syncing Commands

After creating or updating commands, you need to sync them to Discord:

1. Go to the **Commands** section.
2. Select the commands you want to sync.
3. Click the **Sync to Discord** button.

Alternatively, to sync all commands:
1. Go to the **Commands** section.
2. Click the **Sync All** button.

## Statistics and Monitoring

### Bot Statistics

To view statistics for your bots:

1. Navigate to the **Statistics** section.
2. Select a bot from the dropdown.
3. Choose a time period (day, week, month).

You'll see metrics including:
- Total commands executed
- Commands by server
- Active users
- Error rate
- Response time

### Command Usage

To analyze command usage:

1. Go to the **Statistics** section.
2. Click on the **Commands** tab.
3. You'll see:
   - Most used commands
   - Usage trends over time
   - Success/failure rates
   - Average response time

### Server Activity

To view server activity:

1. Go to the **Statistics** section.
2. Click on the **Servers** tab.
3. Select a server from the dropdown.

You'll see metrics including:
- Total command usage
- Active users
- Most active channels
- Usage by time of day

### Logs

To view detailed logs:

1. Navigate to the **Logs** section.
2. Use filters to narrow down the logs:
   - Bot
   - Server
   - Command
   - Status (success/error)
   - Time range
3. Click on a log entry to see details.

## Account Management

### Profile Settings

To manage your profile:

1. Click your profile picture in the top-right corner.
2. Select **Profile**.
3. You can update:
   - Display name
   - Email notifications
   - Language preference
   - Theme (light/dark)

### Security Settings

To manage security settings:

1. Click your profile picture in the top-right corner.
2. Select **Security**.
3. You can:
   - View connected Discord account
   - Enable two-factor authentication
   - Manage API keys
   - View active sessions

### Notification Settings

To configure notifications:

1. Click your profile picture in the top-right corner.
2. Select **Notifications**.
3. Configure preferences for:
   - Email notifications
   - Dashboard notifications
   - Bot status alerts
   - Command error alerts

## Troubleshooting

### Bot Not Connecting

If your bot won't connect to Discord:

1. Check that the bot token is correct in the bot settings.
2. Verify that the bot has the necessary intents enabled in the Discord Developer Portal.
3. Check the bot logs for error messages.
4. Try stopping and restarting the bot.

### Commands Not Working

If commands aren't working:

1. Ensure the commands have been synced to Discord.
2. Check if the command is enabled for the specific server.
3. Verify the user has the required permissions to use the command.
4. Check the command logs for errors.
5. Try re-syncing the commands to Discord.

### Server Not Showing

If a server isn't appearing in your dashboard:

1. Verify the bot has been invited to the server.
2. Check that the bot has the necessary permissions in the server.
3. Try syncing the server list from the bot details page.
4. Ensure you have the necessary permissions in the Discord server.

### Error Logs

To check error logs:

1. Navigate to the **Logs** section.
2. Filter for logs with the **Error** status.
3. Review the error details and timestamp.
4. Common errors include:
   - Invalid token
   - Missing permissions
   - Rate limiting
   - Network issues

## Frequently Asked Questions

### General Questions

**Q: Is Social Cube free to use?**
A: Social Cube offers both free and premium tiers. The free tier allows for a limited number of bots and commands, while premium tiers offer more features and capacity.

**Q: How many bots can I create?**
A: Free accounts can create up to 2 bots. Premium accounts can create between 5 and unlimited bots, depending on the plan.

**Q: Can I transfer ownership of a bot?**
A: Yes, you can transfer ownership to another Social Cube user from the bot settings page.

### Discord Integration

**Q: What permissions does my bot need?**
A: The required permissions depend on what your bot does. At minimum, it needs permissions to read and send messages. Additional permissions are needed for features like role management, message deletion, or channel creation.

**Q: Can I use Social Cube with my existing Discord bot?**
A: Yes, you can use your existing Discord bot token when creating a new bot in Social Cube.

**Q: How do I get a Discord bot token?**
A: Create an application in the [Discord Developer Portal](https://discord.com/developers/applications), add a bot to the application, and then copy the bot token.

### Commands

**Q: How long does it take for new commands to appear in Discord?**
A: After syncing, new commands should appear in Discord within a few minutes. Global commands can take up to an hour to propagate to all servers.

**Q: Can I create commands with subcommands?**
A: Yes, Discord slash commands support subcommands. You can create them in the command editor by adding options of type "Subcommand" or "Subcommand Group".

**Q: Is there a limit to how many commands I can create?**
A: Discord limits each application to 100 global commands and 100 guild-specific commands per guild. Social Cube does not impose additional limits.

### Security and Privacy

**Q: What data does Social Cube store about my Discord servers?**
A: Social Cube stores basic information about your servers, including name, ID, icon, channel list, and role list. We do not store message content unless specifically configured for logging purposes.

**Q: Is my bot token secure?**
A: Yes, bot tokens are encrypted before being stored in our database and are never exposed in the interface.

**Q: Who can see my bot's statistics and logs?**
A: Only you and users you've specifically granted access to can see your bot's statistics and logs.

### Support

**Q: How do I report issues or request features?**
A: You can report issues or request features through the Support link in the dashboard footer, or by emailing support@yourdomain.com.

**Q: Is there documentation for developers?**
A: Yes, developer documentation is available at [https://yourdomain.com/docs/api](https://yourdomain.com/docs/api).

**Q: Do you offer custom bot development?**
A: Yes, we offer custom bot development services. Contact us through the Support link for more information.