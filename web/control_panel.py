# control_panel.py
import streamlit as st
import subprocess
import sys
import asyncio
import threading
import os
import logging
from pathlib import Path
from asyncio import run_coroutine_threadsafe
from discord.ext import commands

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from cogs.holiday_forecast import (
    bot, 
    stop_daily_holiday_reminder, 
    start_daily_holiday_reminder,
    DISCORD_BOT_TOKEN
)
from cogs.announcement import Announcement

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.title("Discord Bot Control Panel")

# ---------------------------------------------------------------------
# 1. Start Discord bot in a background thread (only once per session)
# ---------------------------------------------------------------------
if "bot_started" not in st.session_state:
    st.session_state["bot_started"] = False
    st.session_state["forecast_enabled"] = True

async def run_bot():
    """Run the bot's event loop."""
    # 直接創建和添加 cog
    await bot.add_cog(Announcement(bot))
    # 然後啟動 bot
    await bot.start(DISCORD_BOT_TOKEN)

def start_bot_background():
    """Run the Discord bot in a background thread."""
    if not st.session_state["bot_started"]:
        st.session_state["bot_started"] = True
        loop = asyncio.new_event_loop()
        threading.Thread(target=loop.run_until_complete, args=(run_bot(),), daemon=True).start()

start_bot_background()

# ---------------------------------------------------------------------
# 2. Holiday Forecast Control
# ---------------------------------------------------------------------
st.subheader("Holiday Forecast Status")
forecast_enabled = st.checkbox("Enable Daily Holiday Forecast", value=st.session_state["forecast_enabled"])

# Handle forecast state changes
if forecast_enabled != st.session_state["forecast_enabled"]:
    st.session_state["forecast_enabled"] = forecast_enabled
    if forecast_enabled:
        run_coroutine_threadsafe(start_daily_holiday_reminder(), bot.loop)
        st.success("Daily Holiday Forecast is enabled.")
    else:
        run_coroutine_threadsafe(stop_daily_holiday_reminder(), bot.loop)
        st.warning("Daily Holiday Forecast is disabled.")

# ---------------------------------------------------------------------
# 3. Announcement Control
# ---------------------------------------------------------------------
st.subheader("Announcement System")

# Get the announcement cog
announcement_cog = bot.get_cog('Announcement')

# Channel management
st.subheader("Announcement Channels")
if announcement_cog:
    current_channels = announcement_cog.announcement_channels
    st.write("Current announcement channels:", current_channels)
    
    # 改用 text_input，並加入數字驗證
    new_channel_id_str = st.text_input(
        "Add new channel ID",
        value=str(current_channels[0]) if current_channels else "",
        help="Enter the Discord channel ID (only numbers)"
    )
    
    # 驗證輸入是否為有效的 channel ID
    try:
        new_channel_id = int(new_channel_id_str) if new_channel_id_str.strip() else None
    except ValueError:
        st.error("Please enter a valid channel ID (numbers only)")
        new_channel_id = None
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Add Channel") and new_channel_id:
            announcement_cog.add_announcement_channel(new_channel_id)
            st.success(f"Added channel {new_channel_id}")
    
    with col2:
        if st.button("Remove Channel") and new_channel_id:
            announcement_cog.remove_announcement_channel(new_channel_id)
            st.success(f"Removed channel {new_channel_id}")

# Announcement message input
st.subheader("Send an Announcement")
announcement_message = st.text_area(
    "Announcement Content",
    help="Use @&role_name to mention a role, @username to mention a user"
)

if st.button("Send Announcement"):
    if announcement_message.strip():
        if announcement_cog:
            # Send the announcement using the cog's broadcast function
            future = run_coroutine_threadsafe(
                announcement_cog.broadcast_announcement(announcement_message),
                bot.loop
            )
            try:
                success = future.result(timeout=10)  # Wait up to 10 seconds for the result
                if success:
                    st.success("Announcement sent successfully!")
                else:
                    st.error("Failed to send announcement to any channels.")
            except Exception as e:
                st.error(f"Error sending announcement: {str(e)}")
        else:
            st.error("Announcement system not properly initialized!")
    else:
        st.warning("Please enter a non-empty announcement message.")

# ---------------------------------------------------------------------
# 4. Help Section
# ---------------------------------------------------------------------
with st.expander("Help"):
    st.markdown("""
    ### How to Use the Control Panel
    
    1. **Holiday Forecast**
       - Toggle the checkbox to enable/disable daily holiday forecasts
       - The bot will automatically send holiday information to configured channels
    
    2. **Announcement System**
       - Enter your announcement message in the text area
       - Use `@&role_name` to mention a role (e.g., `@&Admin`)
       - Use `@username` to mention a user (e.g., `@John`)
       - Click "Send Announcement" to broadcast your message
       - Manage announcement channels using the channel ID input
    
    3. **Best Practices**
       - Keep announcements clear and concise
       - Use mentions sparingly to avoid spam
       - Test your announcement in a test channel first
       - Make sure the bot has proper permissions in all channels
    """)
