# Discord Application Setup Guide

This guide will walk you through setting up a Discord application for OAuth2 authentication in Social Cube.

## Creating a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click the "New Application" button
3. Enter a name for your application (e.g., "Social Cube")
4. Accept the terms of service and click "Create"

## Configuring OAuth2

1. In your application dashboard, click on the "OAuth2" tab in the left sidebar
2. Add the following redirect URL: `http://localhost:8000/accounts/discord/login/callback/`
   - For production, you'll need to add your production URL as well
3. Note down your "Client ID" and "Client Secret" - you'll need these for configuration

## Required Scopes

When setting up OAuth2, ensure your application requests the following scopes:

- `identify` - Access to user's username, avatar, etc.
- `email` - Access to user's email address
- `guilds` - Access to list the servers the user is in

## Bot Configuration (Optional)

If you're also setting up a bot:

1. Go to the "Bot" tab in the left sidebar
2. Click "Add Bot"
3. Configure your bot preferences
4. Under "Privileged Gateway Intents", enable:
   - SERVER MEMBERS INTENT
   - MESSAGE CONTENT INTENT
   - PRESENCE INTENT
5. Save changes
6. Note down your bot token - you'll need this for configuration

## Setting Up Environment Variables

1. Copy the `.env.example` file to `.env`
2. Set the following variables:
   ```
   DISCORD_CLIENT_ID=your_client_id
   DISCORD_CLIENT_SECRET=your_client_secret
   DISCORD_REDIRECT_URI=http://localhost:8000/accounts/discord/login/callback/
   DISCORD_BOT_TOKEN=your_bot_token (if using a bot)
   ```

## Running the Setup Script

After configuring your Discord application and setting the environment variables, run:

```bash
python scripts/setup_discord_oauth.py
```

This will create the necessary database records for Discord OAuth2 authentication.

## Testing the Authentication

1. Start your Django development server
2. Go to http://localhost:8000/
3. Click "Login with Discord"
4. You should be redirected to Discord's authorization page
5. After authorizing, you should be redirected back to your application and logged in