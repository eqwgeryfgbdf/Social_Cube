#holiday_forecast.py
import discord
from discord.ext import commands, tasks
import requests
import json
from datetime import datetime, timedelta
import os
import asyncio
import sys
from pathlib import Path
from fastapi import FastAPI
import threading
import uvicorn

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from utils.config import DISCORD_BOT_TOKEN, ANNOUNCEMENT_CHANNEL_ID

# Set up intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='@bot ', intents=intents)

# Global state
is_forecast_enabled = True

# FastAPI setup
app = FastAPI()

@app.post("/stop_forecast")
async def stop_forecast():
    try:
        await stop_daily_holiday_reminder()
        return {"status": "success", "message": "forecast stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def broadcast_announcement(message: str):
    """Broadcast a message to the announcement channel."""
    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        await channel.send(f"**公告:** {message}")
        return True
    return False

async def stop_daily_holiday_reminder():
    """Cancels the loop and notifies the channel."""
    global is_forecast_enabled
    is_forecast_enabled = False
    daily_holiday_reminder.cancel()

    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        await channel.send("假期播報功能已關閉 (Holiday forecast is now disabled).")

async def start_daily_holiday_reminder():
    """Starts the holiday reminder and notifies the channel."""
    global is_forecast_enabled
    is_forecast_enabled = True
    daily_holiday_reminder.start()

    channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
    if channel:
        await channel.send("假期播報功能已開啟 (Holiday forecast is now enabled).")

@bot.event
async def on_ready():
    print(f'已登錄 {bot.user.name}')
    try:
        await asyncio.sleep(1)
        await send_startup_message()
        
        channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if channel:
            await get_nearest_holiday(channel, next_execution_time=None)
        else:
            print(f"Could not find channel with ID: {ANNOUNCEMENT_CHANNEL_ID}")
        
        if is_forecast_enabled:
            daily_holiday_reminder.start()
    except Exception as e:
        print(f"Error during startup: {e}")

@tasks.loop(hours=24)
async def daily_holiday_reminder():
    if not is_forecast_enabled:
        return
        
    try:
        channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if not channel:
            print(f"Could not find channel with ID: {ANNOUNCEMENT_CHANNEL_ID}")
            return
            
        next_execution_time = await get_next_execution_time()
        await get_nearest_holiday(channel, next_execution_time)
    except Exception as e:
        print(f"Error in daily_holiday_reminder: {e}")

@daily_holiday_reminder.before_loop
async def before_daily_holiday_reminder():
    """Waits until 1:15 AM local time before starting the daily loop."""
    now = datetime.now()
    target_time = now.replace(hour=8, minute=30, second=0, microsecond=0)
    
    if now > target_time:
        target_time += timedelta(days=1)
    
    delta = target_time - now
    seconds_until_target = delta.total_seconds()
    await asyncio.sleep(seconds_until_target)

@bot.command()
async def nearest_holiday(ctx):
    """Manually check the nearest holiday."""
    await get_nearest_holiday(ctx.channel, None)

async def send_startup_message():
    """Notifies the channel that the bot has started."""
    try:
        channel = bot.get_channel(ANNOUNCEMENT_CHANNEL_ID)
        if not channel:
            print(f"Could not find channel with ID: {ANNOUNCEMENT_CHANNEL_ID}")
            return
        await channel.send("機器人已經啟動！")
    except Exception as e:
        print(f"Error sending startup message: {e}")

async def get_next_execution_time():
    """Calculates the next execution time and how long until then."""
    now = datetime.now()
    target_time = now.replace(hour=1, minute=15, second=0, microsecond=0)
    
    if now > target_time:
        target_time += timedelta(days=1)
    
    time_until_target = target_time - now
    return target_time, time_until_target

async def get_nearest_holiday(channel, next_execution_time):
    """Fetches and announces the nearest upcoming holiday."""
    try:
        now = datetime.now()
        year = now.year
        holidays_url = f"https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json"
        
        response = requests.get(holidays_url)
        if response.status_code == 200:
            holidays_data = json.loads(response.text)

            nearest_holiday = None
            nearest_distance = timedelta(days=365)
            
            for holiday in holidays_data:
                if not holiday['isHoliday'] or not holiday['description']:
                    continue
                holiday_date = datetime.strptime(holiday['date'], '%Y%m%d')
                distance = holiday_date - now
                if distance >= timedelta(days=0) and distance < nearest_distance:
                    nearest_holiday = holiday
                    nearest_distance = distance
            
            if nearest_holiday:
                description = nearest_holiday['description']
                formatted_date = (now + nearest_distance).strftime('%Y年%m月%d日')
                message = (
                    f"最近的假期是 __**{description}**__，"
                    f"日期是 {formatted_date}（還有 {nearest_distance.days} 天）。\n"
                )
                
                if next_execution_time:
                    next_execution_time_str = next_execution_time[0].strftime('%Y-%m-%d %H:%M:%S')
                    time_until_next_execution = next_execution_time[1]
                    message += (
                        f"下一次執行時間為 {next_execution_time_str}，"
                        f"還有 {time_until_next_execution} 時間。"
                    )
                
                await channel.send(message)
            else:
                await channel.send("今年沒有即將到來的假期。")
        else:
            await channel.send("獲取假期數據失敗。")
    except Exception as e:
        print(f"Error in get_nearest_holiday: {e}")
        await channel.send("處理假期數據時發生錯誤。")

def run_api():
    """Run the FastAPI server."""
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    try:
        # Start FastAPI in background
        threading.Thread(target=run_api, daemon=True).start()
        # Start the Discord bot
        bot.run(DISCORD_BOT_TOKEN)
    except Exception as e:
        print(f"Error starting bot: {e}")
