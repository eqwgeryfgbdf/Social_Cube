# control_panel.py
import streamlit as st
import subprocess
import sys
import asyncio
import threading
import os
import logging
import json
from pathlib import Path
from asyncio import run_coroutine_threadsafe
from discord.ext import commands
from functools import partial
import discord
import time

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from cogs.holiday_forecast import (
    bot as main_bot,
    stop_daily_holiday_reminder,
    start_daily_holiday_reminder,
    DISCORD_BOT_TOKEN
)
from cogs.announcement import Announcement

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 設置頁面配置
st.set_page_config(
    page_title="Discord 機器人控制面板",
    page_icon="🤖",
    layout="wide"
)

# 自定義 CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #5865F2;
    }
    .stButton>button:hover {
        background-color: #4752C4;
    }
    .success {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #57F287;
        color: white;
    }
    .warning {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FEE75C;
        color: black;
    }
    .error {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ED4245;
        color: white;
    }
    .sidebar .sidebar-content {
        background-color: #2F3136;
    }
    .bot-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #40444B;
        margin-bottom: 1rem;
    }
    .channel-card {
        padding: 0.5rem;
        border-radius: 0.3rem;
        border: 1px solid #40444B;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 初始化 session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.current_page = "主頁"
    st.session_state.bot_started = False
    st.session_state.bots = {
        "主要機器人": {
            "token": DISCORD_BOT_TOKEN,
            "status": "離線",
            "channels": [],
            "features": ["節日預報", "公告系統", "債務追蹤"],
            "instance": None  # 初始化時不創建實例
        }
    }
    st.session_state.selected_bot = "主要機器人"
    st.session_state.channels = {}
    st.session_state.bot_instances = {}
    st.session_state.節日預報狀態 = False

CONFIG_FILE = "bot_config.json"

# 加載配置
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            saved_bots = config.get('bots', {})
            for bot_name, bot_data in saved_bots.items():
                if bot_name in st.session_state.bots:
                    st.session_state.bots[bot_name].update({
                        "token": bot_data["token"],
                        "channels": bot_data["channels"],
                        "features": bot_data["features"]
                    })
            st.session_state.channels = config.get('channels', {})

# 保存配置
def save_config():
    bots_to_save = {}
    for bot_name, bot_data in st.session_state.bots.items():
        bots_to_save[bot_name] = {
            "token": bot_data["token"],
            "channels": bot_data["channels"],
            "features": bot_data["features"],
            "status": bot_data["status"]
        }
    
    config = {
        'bots': bots_to_save,
        'channels': st.session_state.channels
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 創建新的 Discord 機器人實例
def create_bot_instance(token):
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        new_bot = commands.Bot(command_prefix='!', intents=intents)
        
        # 添加錯誤處理
        @new_bot.event
        async def on_error(event, *args, **kwargs):
            logging.error(f"機器人錯誤：{event}", exc_info=True)
        
        return new_bot
    except Exception as e:
        logging.error(f"創建機器人實例時發生錯誤：{e}")
        raise e

# 異步操作的包裝器
def run_async(coro):
    """安全地執行異步操作的輔助函數"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(coro)
        loop.close()
        return result
    except Exception as e:
        logging.error(f"執行異步操作時發生錯誤：{e}")
        raise e

# 在背景執行機器人
def run_bot_in_background(bot, token):
    """在背景線程中運行機器人"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 定義啟動任務
        async def startup():
            try:
                # 啟動機器人
                await bot.start(token)
            except Exception as e:
                logging.error(f"機器人啟動失敗：{e}")
                raise e
        
        # 運行啟動任務
        loop.run_until_complete(startup())
    except Exception as e:
        logging.error(f"背景執行機器人時發生錯誤：{e}")
        raise e

# 在機器人的事件循環中執行命令
def run_in_bot_loop(bot, coro):
    """在機器人的事件循環中執行協程"""
    if not bot.loop or not bot.is_closed():
        future = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try:
            return future.result(timeout=30)  # 30秒超時
        except Exception as e:
            logging.error(f"在機器人事件循環中執行時發生錯誤：{e}")
            raise e
    else:
        raise Exception("機器人未就緒或已關閉")

# 加載和同步命令
async def setup_bot_commands(bot):
    """設置機器人的命令和 Cogs"""
    try:
        # 確保路徑正確
        import sys
        from pathlib import Path
        project_root = str(Path(__file__).parent.parent)
        if project_root not in sys.path:
            sys.path.append(project_root)
        
        # 清除現有的命令和 Cogs
        bot.tree.clear_commands(guild=None)
        for cog_name in list(bot.cogs.keys()):
            await bot.remove_cog(cog_name)
        logging.info("已清除現有命令和 Cogs")
        
        # 等待一下確保清除完成
        await asyncio.sleep(1)
        
        # 加載 Cogs
        try:
            # 先加載 announcement
            await bot.add_cog(Announcement(bot))
            logging.info("已加載 Announcement Cog")
            
            # 加載 debt_tracker_slash
            await bot.load_extension("cogs.debt_tracker_slash")
            logging.info("已加載 DebtTrackerSlash Cog")
            
            # 檢查 Cogs 是否正確加載
            loaded_cogs = list(bot.cogs.keys())
            logging.info(f"已加載的 Cogs：{loaded_cogs}")
            
            if "DebtTrackerSlash" not in loaded_cogs:
                raise Exception("DebtTrackerSlash Cog 未正確加載")
            
        except Exception as e:
            logging.error(f"加載 Cogs 時發生錯誤：{e}")
            raise e

        # 等待一下確保 Cogs 完全加載
        await asyncio.sleep(1)
        
        # 同步命令
        try:
            # 檢查當前的命令
            commands_before = await bot.tree.fetch_commands()
            logging.info(f"同步前的命令：{[cmd.name for cmd in commands_before]}")
            
            # 同步全局命令
            await bot.tree.sync()
            logging.info("已同步全局命令")
            
            # 等待一下確保同步完成
            await asyncio.sleep(1)
            
            # 檢查同步後的命令
            commands_after = await bot.tree.fetch_commands()
            command_names = [cmd.name for cmd in commands_after]
            logging.info(f"同步後的命令：{command_names}")
            
            # 檢查 debt 命令是否存在
            debt_commands = [cmd for cmd in bot.tree.walk_commands() if cmd.name == "debt"]
            if not debt_commands:
                # 嘗試重新同步
                logging.warning("未找到 debt 命令，嘗試重新同步...")
                await bot.tree.sync()
                await asyncio.sleep(1)
                
                # 再次檢查
                debt_commands = [cmd for cmd in bot.tree.walk_commands() if cmd.name == "debt"]
                if not debt_commands:
                    raise Exception("debt 命令未能成功註冊")
            
            logging.info("命令同步成功完成")
            return True
            
        except Exception as e:
            logging.error(f"同步命令時發生錯誤：{e}")
            raise e
            
    except Exception as e:
        logging.error(f"設置機器人命令時發生錯誤：{e}")
        raise e

# 啟動機器人
async def start_bot(bot_name, token):
    try:
        # 檢查是否已經有運行中的實例並嘗試關閉
        if bot_name in st.session_state.bot_instances:
            old_bot = st.session_state.bot_instances[bot_name]
            try:
                if not old_bot.is_closed():
                    await old_bot.close()
                    await asyncio.sleep(2)  # 等待關閉完成
                # 確保所有連接都已關閉
                if hasattr(old_bot, 'http') and hasattr(old_bot.http, '_connector'):
                    await old_bot.http._connector.close()
            except Exception as e:
                logging.warning(f"關閉舊實例時發生錯誤：{e}")
            
        # 創建新的機器人實例
        bot = create_bot_instance(token)
        
        # 定義就緒事件處理
        ready_event = asyncio.Event()
        
        @bot.event
        async def on_ready():
            try:
                ready_event.set()
                logging.info(f"機器人已就緒：{bot.user.name}")
                
                # 等待一下確保完全就緒
                await asyncio.sleep(2)
                
                # 設置命令
                await setup_bot_commands(bot)
                logging.info("命令設置完成")
                
            except Exception as e:
                logging.error(f"on_ready 事件處理時發生錯誤：{e}")
                raise e
        
        # 在新線程中啟動機器人
        try:
            bot_thread = threading.Thread(
                target=lambda: asyncio.run(bot.start(token)),
                daemon=True
            )
            bot_thread.start()
            
            # 等待機器人準備就緒，使用更長的超時時間
            timeout = 60  # 增加到 60 秒
            start_time = time.time()
            while not bot.is_ready() and time.time() - start_time < timeout:
                await asyncio.sleep(1)  # 增加檢查間隔
                if ready_event.is_set():
                    break
            
            if not bot.is_ready():
                # 嘗試清理資源
                try:
                    if hasattr(bot, 'http') and hasattr(bot.http, '_connector'):
                        await bot.http._connector.close()
                    await bot.close()
                except:
                    pass
                raise Exception("機器人啟動超時")

            # 等待命令設置完成
            await asyncio.sleep(5)
                
            # 更新狀態
            st.session_state.bot_instances[bot_name] = bot
            st.session_state.bots[bot_name]["instance"] = bot
            st.session_state.bots[bot_name]["status"] = "運行中"
            
            return True
            
        except Exception as e:
            logging.error(f"啟動機器人線程時發生錯誤：{e}")
            raise e
            
    except Exception as e:
        logging.error(f"啟動過程中發生錯誤：{e}")
        st.session_state.bots[bot_name]["status"] = "錯誤"
        # 確保清理所有資源
        try:
            if 'bot' in locals() and hasattr(bot, 'http') and hasattr(bot.http, '_connector'):
                await bot.http._connector.close()
            if 'bot' in locals():
                await bot.close()
        except:
            pass
        raise e

# 停止機器人
async def stop_bot(bot_name):
    if bot_name in st.session_state.bot_instances:
        bot = st.session_state.bot_instances[bot_name]
        try:
            # 移除所有 Cogs
            for cog in list(bot.cogs.keys()):
                await bot.remove_cog(cog)
            logging.info(f"已移除所有 Cogs")
            
            # 關閉連接器
            if hasattr(bot, 'http') and hasattr(bot.http, '_connector'):
                await bot.http._connector.close()
            
            # 關閉機器人
            if not bot.is_closed():
                await bot.close()
                await asyncio.sleep(2)  # 等待關閉完成
            logging.info(f"機器人已關閉")
            
            # 清理狀態
            st.session_state.bots[bot_name]["status"] = "離線"
            st.session_state.bots[bot_name]["instance"] = None
            del st.session_state.bot_instances[bot_name]
            
            return True
            
        except Exception as e:
            logging.error(f"停止機器人時發生錯誤：{e}")
            raise e

# 發送消息到頻道
async def send_message_to_channel(bot, channel_id, message):
    """安全地發送消息到頻道的輔助函數"""
    try:
        channel = bot.get_channel(channel_id)
        if not channel:
            raise Exception(f"無法找到頻道 {channel_id}")
        
        # 創建新的事件循環來發送消息
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 在事件循環中發送消息
            future = asyncio.run_coroutine_threadsafe(channel.send(message), bot.loop)
            result = future.result(timeout=10)  # 10秒超時
            return True
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"發送消息到頻道 {channel_id} 時發生錯誤：{e}")
        raise e

# 測試發送消息
async def send_test_message(bot, channel_id):
    """發送測試消息的輔助函數"""
    try:
        return await send_message_to_channel(bot, channel_id, "🔄 正在測試節日預報功能...")
    except Exception as e:
        logging.error(f"發送測試消息失敗：{e}")
        raise e

# 檢查機器人狀態
def check_bot_status(bot_name):
    """檢查機器人是否正常運行"""
    bot_info = st.session_state.bots.get(bot_name)
    if not bot_info:
        return False
        
    bot_instance = bot_info.get("instance")
    if not bot_instance:
        return False
        
    try:
        return bot_instance.is_ready() and not bot_instance.is_closed() and bot_info["status"] == "運行中"
    except:
        return False

# 加載配置
load_config()

# 側邊欄導航
with st.sidebar:
    st.title("🤖 機器人控制台")
    st.markdown("---")
    
    # 機器人選擇器
    selected_bot = st.selectbox(
        "選擇機器人",
        options=list(st.session_state.bots.keys()),
        key="bot_selector"
    )
    if selected_bot != st.session_state.selected_bot:
        st.session_state.selected_bot = selected_bot
        st.rerun()
    
    st.markdown("---")
    
    # 導航按鈕
    pages = {
        "主頁": "🏠",
        "機器人管理": "🤖",
        "頻道管理": "📺",
        "節日預報": "📅",
        "公告系統": "📢",
        "債務管理": "💰",
        "設定": "⚙️"
    }
    
    for page, icon in pages.items():
        if st.button(f"{icon} {page}", key=f"nav_{page}", use_container_width=True):
            st.session_state.current_page = page
            st.rerun()

# 主要內容區域
if st.session_state.current_page == "主頁":
    st.title("🏠 歡迎使用 Discord 機器人控制面板")
    
    # 顯示當前選擇的機器人資訊
    st.markdown(f"### 當前機器人：{st.session_state.selected_bot}")
    bot_info = st.session_state.bots[st.session_state.selected_bot]
    
    # 檢查機器人狀態
    is_running = check_bot_status(st.session_state.selected_bot)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status = "🟢 運行中" if is_running else "🔴 離線"
        st.metric("狀態", status)
    with col2:
        st.metric("已連接頻道數", len(bot_info["channels"]))
    with col3:
        st.metric("已啟用功能數", len(bot_info["features"]))
    
    # 快速操作按鈕
    st.markdown("### ⚡ 快速操作")
    quick_col1, quick_col2 = st.columns(2)
    with quick_col1:
        if not is_running:
            if st.button("▶️ 啟動機器人", key="quick_start", use_container_width=True):
                try:
                    if run_async(start_bot(st.session_state.selected_bot, bot_info["token"])):
                        st.success(f"✅ 機器人 {st.session_state.selected_bot} 已啟動")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 啟動失敗：{str(e)}")
        else:
            if st.button("⏹️ 停止機器人", key="quick_stop", use_container_width=True):
                try:
                    if run_async(stop_bot(st.session_state.selected_bot)):
                        st.success(f"✅ 機器人 {st.session_state.selected_bot} 已停止")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ 停止失敗：{str(e)}")
    
    with quick_col2:
        if st.button("🔄 重新啟動", key="quick_restart", use_container_width=True):
            try:
                if run_async(stop_bot(st.session_state.selected_bot)) and \
                   run_async(start_bot(st.session_state.selected_bot, bot_info["token"])):
                    st.success(f"✅ 機器人 {st.session_state.selected_bot} 已重新啟動")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ 重新啟動失敗：{str(e)}")

elif st.session_state.current_page == "機器人管理":
    st.title("🤖 機器人管理")
    
    # 新增機器人
    with st.expander("➕ 新增機器人", expanded=False):
        st.markdown("""
        ### 如何獲取 Discord 機器人 Token:
        1. 前往 [Discord Developer Portal](https://discord.com/developers/applications)
        2. 點擊 "New Application" 創建新應用
        3. 在左側選單中點擊 "Bot"
        4. 點擊 "Add Bot" 或 "Reset Token" 
        5. 複製顯示的 Token
        """)
        
        new_bot_name = st.text_input("機器人名稱", key="new_bot_name", placeholder="例如：活動通知機器人")
        new_bot_token = st.text_input("機器人 Token", key="new_bot_token", type="password", placeholder="請輸入從 Discord Developer Portal 獲取的 Bot Token")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✨ 測試 Token", key="test_token", use_container_width=True) and new_bot_token:
                try:
                    test_bot = create_bot_instance(new_bot_token)
                    st.success("✅ Token 有效")
                except Exception as e:
                    st.error(f"❌ Token 無效：{str(e)}")
        
        with col2:
            if st.button("➕ 新增機器人", key="add_bot", use_container_width=True) and new_bot_name and new_bot_token:
                if new_bot_name not in st.session_state.bots:
                    st.session_state.bots[new_bot_name] = {
                        "token": new_bot_token,
                        "status": "離線",
                        "channels": [],
                        "features": []
                    }
                    save_config()
                    st.success(f"✅ 已新增機器人：{new_bot_name}")
                    st.rerun()
                else:
                    st.error("❌ 機器人名稱已存在")
    
    # 顯示現有機器人
    st.markdown("### 現有機器人")
    for bot_name, bot_info in st.session_state.bots.items():
        with st.container():
            st.markdown(f"""
            <div class="bot-card">
                <h4>{bot_name}</h4>
                <p>狀態：{bot_info['status']}</p>
                <p>已連接頻道：{len(bot_info['channels'])}</p>
                <p>已啟用功能：{', '.join(bot_info['features'])}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 生成邀請鏈接
            if bot_info["status"] == "運行中":
                try:
                    bot_instance = bot_info["instance"]
                    if bot_instance and bot_instance.user:
                        invite_url = discord.utils.oauth_url(
                            bot_instance.user.id,
                            permissions=discord.Permissions(
                                send_messages=True,
                                read_messages=True,
                                manage_messages=True,
                                embed_links=True,
                                attach_files=True,
                                read_message_history=True,
                                mention_everyone=True,
                                use_external_emojis=True,
                                add_reactions=True,
                                view_channel=True
                            ),
                            scopes=['bot', 'applications.commands']  # 添加 applications.commands 範圍
                        )
                        st.markdown(f"""
                        #### 🔗 邀請連結
                        1. [點此邀請機器人到新伺服器]({invite_url})
                        2. 邀請後需要等待約 1 小時讓 Slash Commands 同步
                        3. 如需立即使用，可以踢出機器人後重新邀請
                        """)
                except Exception as e:
                    st.error(f"生成邀請連結時發生錯誤：{str(e)}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if bot_info["status"] == "離線":
                    if st.button("▶️ 啟動", key=f"start_{bot_name}", use_container_width=True):
                        try:
                            if run_async(start_bot(bot_name, bot_info["token"])):
                                st.success(f"✅ 機器人 {bot_name} 已啟動")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ 啟動失敗：{str(e)}")
                else:
                    if st.button("⏹️ 停止", key=f"stop_{bot_name}", use_container_width=True):
                        try:
                            if run_async(stop_bot(bot_name)):
                                st.success(f"✅ 機器人 {bot_name} 已停止")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ 停止失敗：{str(e)}")
            
            with col2:
                if st.button("🔄 重新啟動", key=f"restart_{bot_name}", use_container_width=True):
                    try:
                        if run_async(stop_bot(bot_name)) and \
                           run_async(start_bot(bot_name, bot_info["token"])):
                            st.success(f"✅ 機器人 {bot_name} 已重新啟動")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ 重新啟動失敗：{str(e)}")
            
            with col3:
                if bot_name != "主要機器人":  # 防止刪除主要機器人
                    if st.button("❌ 移除", key=f"remove_{bot_name}", use_container_width=True):
                        if bot_info["status"] != "離線":
                            run_async(stop_bot(bot_name))
                        del st.session_state.bots[bot_name]
                        save_config()
                        st.success(f"✅ 已移除機器人：{bot_name}")
                        st.rerun()

    # 添加權限說明
    with st.expander("🔒 權限說明", expanded=False):
        st.markdown("""
        ### 必要權限說明
        
        機器人需要以下權限才能正常運作：
        
        1. **基本權限**
           - 查看頻道
           - 發送訊息
           - 嵌入連結
           - 附加檔案
           - 讀取訊息歷史
           
        2. **進階權限**
           - 管理訊息（用於清理命令）
           - 提及 @everyone 和 @here
           - 使用外部表情符號
           - 添加反應
           
        3. **Slash Commands 權限**
           - applications.commands 範圍
           - 用於啟用斜線命令功能
           
        ### 重新同步命令
        如果更換伺服器或命令無法使用：
        1. 將機器人踢出伺服器
        2. 重新啟動機器人
        3. 使用新的邀請連結重新邀請
        4. 等待約 1 小時讓 Discord 完成命令同步
        """)

elif st.session_state.current_page == "頻道管理":
    st.title("📺 頻道管理")
    
    # 新增頻道
    with st.expander("➕ 新增頻道", expanded=False):
        new_channel_name = st.text_input("頻道名稱")
        new_channel_id = st.text_input("頻道 ID")
        new_channel_type = st.selectbox("頻道類型", ["文字頻道", "語音頻道", "公告頻道"])
        
        if st.button("新增", key="add_channel") and new_channel_name and new_channel_id:
            try:
                channel_id = int(new_channel_id)
                if new_channel_id not in st.session_state.channels:
                    st.session_state.channels[new_channel_id] = {
                        "name": new_channel_name,
                        "type": new_channel_type,
                        "features": []
                    }
                    # 將頻道添加到當前選擇的機器人
                    bot_info = st.session_state.bots[st.session_state.selected_bot]
                    if channel_id not in bot_info["channels"]:
                        bot_info["channels"].append(channel_id)
                    save_config()
                    st.success(f"✅ 已新增頻道：{new_channel_name}")
                else:
                    st.error("❌ 頻道 ID 已存在")
            except ValueError:
                st.error("❌ 請輸入有效的頻道 ID")
    
    # 顯示現有頻道
    st.markdown("### 現有頻道")
    current_bot_channels = st.session_state.bots[st.session_state.selected_bot]["channels"]
    
    for channel_id in current_bot_channels:
        if str(channel_id) in st.session_state.channels:
            channel_info = st.session_state.channels[str(channel_id)]
            with st.container():
                st.markdown(f"""
                <div class="channel-card">
                    <h4>{channel_info['name']} ({channel_id})</h4>
                    <p>類型：{channel_info['type']}</p>
                    <p>已啟用功能：{', '.join(channel_info['features'])}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("⚙️ 設定", key=f"settings_{channel_id}"):
                        st.session_state.current_channel = channel_id
                with col2:
                    if st.button("❌ 移除", key=f"remove_{channel_id}"):
                        current_bot_channels.remove(channel_id)
                        save_config()
                        st.success(f"✅ 已移除頻道：{channel_info['name']}")

elif st.session_state.current_page == "節日預報":
    st.title("📅 節日預報設定")
    
    # 獲取當前機器人實例
    current_bot = st.session_state.bots[st.session_state.selected_bot]
    is_running = check_bot_status(st.session_state.selected_bot)
    
    if not is_running:
        st.error("❌ 請先啟動機器人")
    else:
        # 檢查是否已啟用節日預報
        forecast_enabled = st.toggle("啟用每日節日預報", value=st.session_state.節日預報狀態)
        
        if forecast_enabled != st.session_state.節日預報狀態:
            st.session_state.節日預報狀態 = forecast_enabled
            try:
                if forecast_enabled:
                    run_async(start_daily_holiday_reminder())
                    if "節日預報" not in current_bot["features"]:
                        current_bot["features"].append("節日預報")
                    st.success("✅ 每日節日預報已啟用")
                else:
                    run_async(stop_daily_holiday_reminder())
                    if "節日預報" in current_bot["features"]:
                        current_bot["features"].remove("節日預報")
                    st.warning("⚠️ 每日節日預報已停用")
                save_config()
            except Exception as e:
                logging.error(f"節日預報設定錯誤：{e}")
                st.error(f"❌ 操作失敗：{str(e)}")
        
        # 選擇發送頻道
        st.markdown("### 選擇發送頻道")
        current_bot_channels = current_bot["channels"]
        
        if len(current_bot_channels) == 0:
            st.warning("⚠️ 尚未設定任何頻道，請先在頻道管理中新增頻道")
        else:
            for channel_id in current_bot_channels:
                if str(channel_id) in st.session_state.channels:
                    channel_info = st.session_state.channels[str(channel_id)]
                    enabled = st.checkbox(
                        f"{channel_info['name']} ({channel_id})",
                        value="節日預報" in channel_info.get("features", []),
                        key=f"holiday_channel_{channel_id}"
                    )
                    
                    if enabled and "節日預報" not in channel_info.get("features", []):
                        channel_info.setdefault("features", []).append("節日預報")
                        save_config()
                    elif not enabled and "節日預報" in channel_info.get("features", []):
                        channel_info["features"].remove("節日預報")
                        save_config()
        
        # 顯示預報設定
        with st.expander("⚙️ 預報設定", expanded=False):
            st.markdown("""
            ### 預報時間
            目前固定於每日早上 8:00 發送預報
            
            ### 預報內容
            - 今日節日
            - 節日描述
            - 相關活動建議
            """)
            
            if st.button("🔄 立即發送測試預報", key="test_holiday_forecast"):
                try:
                    # 獲取已啟用節日預報的頻道
                    enabled_channels = [
                        ch_id for ch_id in current_bot_channels
                        if "節日預報" in st.session_state.channels[str(ch_id)].get("features", [])
                    ]
                    
                    if not enabled_channels:
                        st.error("❌ 請先選擇至少一個發送頻道")
                    else:
                        bot_instance = current_bot["instance"]
                        success_count = 0
                        
                        for channel_id in enabled_channels:
                            try:
                                if run_async(send_test_message(bot_instance, channel_id)):
                                    success_count += 1
                            except Exception as e:
                                st.error(f"❌ 發送到頻道 {channel_id} 失敗：{str(e)}")
                        
                        if success_count > 0:
                            st.success(f"✅ 測試預報已發送到 {success_count} 個頻道")
                        
                except Exception as e:
                    logging.error(f"發送測試預報時發生錯誤：{e}")
                    st.error(f"❌ 發送失敗：{str(e)}")

elif st.session_state.current_page == "公告系統":
    st.title("📢 公告系統")
    
    # 頻道管理
    with st.expander("📌 頻道管理", expanded=True):
        current_bot = st.session_state.bots[st.session_state.selected_bot]
        current_bot_channels = current_bot["channels"]
        
        # 使用 checkbox 來管理頻道
        for channel_id in current_bot_channels:
            if str(channel_id) in st.session_state.channels:
                channel_info = st.session_state.channels[str(channel_id)]
                enabled = st.checkbox(
                    f"{channel_info['name']} ({channel_id})",
                    value="公告系統" in channel_info.get("features", []),
                    key=f"announcement_channel_{channel_id}"
                )
                
                if enabled and "公告系統" not in channel_info.get("features", []):
                    channel_info.setdefault("features", []).append("公告系統")
                    save_config()
                elif not enabled and "公告系統" in channel_info.get("features", []):
                    channel_info["features"].remove("公告系統")
                    save_config()
    
    # 發送公告
    st.markdown("### ✍️ 發送新公告")
    
    # 公告內容輸入
    announcement_text = st.text_area(
        "公告內容",
        help="使用 @&角色名稱 來提及角色，使用 @用戶名 來提及用戶",
        height=150,
        key="announcement_text"
    )
    
    # 獲取已啟用公告系統的頻道列表
    enabled_channels = [
        channel_id for channel_id in current_bot_channels
        if str(channel_id) in st.session_state.channels
        and "公告系統" in st.session_state.channels[str(channel_id)].get("features", [])
    ]
    
    # 選擇發送頻道
    if enabled_channels:
        channel_options = [
            f"{st.session_state.channels[str(ch_id)]['name']} ({ch_id})"
            for ch_id in enabled_channels
        ]
        selected_channels = st.multiselect(
            "選擇發送頻道",
            options=channel_options,
            default=channel_options,  # 預設全選
            key="selected_announcement_channels"
        )
        
        # 發送按鈕
        if st.button("📤 發送公告", use_container_width=True, key="send_announcement"):
            if not announcement_text.strip():
                st.error("❌ 請輸入公告內容")
            elif not selected_channels:
                st.error("❌ 請選擇至少一個發送頻道")
            else:
                success_count = 0
                for channel in selected_channels:
                    try:
                        # 從頻道字串中提取ID
                        channel_id = int(channel.split("(")[-1].strip(")"))
                        
                        # 獲取機器人實例
                        bot_instance = current_bot.get("instance")
                        if not bot_instance:
                            st.error("❌ 機器人未啟動，請先啟動機器人")
                            break
                            
                        # 發送消息
                        if run_async(send_message_to_channel(
                            bot_instance,
                            channel_id,
                            f"**公告：** {announcement_text}"
                        )):
                            success_count += 1
                    except Exception as e:
                        st.error(f"❌ 發送到頻道 {channel} 時發生錯誤：{str(e)}")
                
                if success_count > 0:
                    st.success(f"✅ 成功發送公告到 {success_count} 個頻道！")
                    st.rerun()
    else:
        st.warning("⚠️ 請先在頻道管理中啟用至少一個公告頻道")

elif st.session_state.current_page == "債務管理":
    st.title("💰 債務管理")
    
    # 檢查機器人狀態
    current_bot = st.session_state.bots[st.session_state.selected_bot]
    is_running = check_bot_status(st.session_state.selected_bot)
    
    if not is_running:
        st.error("❌ 請先啟動機器人")
    else:
        # 顯示使用說明
        with st.expander("ℹ️ 使用說明", expanded=False):
            st.markdown("""
            ### 債務追蹤系統使用說明
            
            本系統提供以下 Slash Commands：
            
            1. **/debt add** `@欠款人` `@債主` `金額`
               - 記錄一筆新的欠款
               - 系統會自動處理債務互抵
            
            2. **/debt summary** [`@用戶`]
               - 查看所有債務狀況
               - 可選擇指定用戶查看其相關債務
            
            3. **/debt clear** `@欠款人` `@債主`
               - 清除兩人之間的債務記錄
            
            ### 特色功能
            - 自動債務互抵計算
            - 按月份保存交易記錄
            - 直觀的債務摘要顯示
            """)
        
        # 債務記錄查看
        st.markdown("### 📊 債務記錄")
        
        # 選擇年月
        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox(
                "選擇年份",
                options=range(2024, 2026),
                format_func=lambda x: f"{x}年"
            )
        with col2:
            selected_month = st.selectbox(
                "選擇月份",
                options=range(1, 13),
                format_func=lambda x: f"{x:02d}月"
            )
        
        # 構建 CSV 路徑
        csv_path = f"data/debt/{selected_year}/debt_{selected_year}-{selected_month:02d}.csv"
        
        try:
            if os.path.exists(csv_path):
                # 讀取 CSV 文件
                import pandas as pd
                df = pd.read_csv(csv_path)
                
                # 顯示交易記錄
                st.markdown("#### 交易記錄")
                if not df.empty:
                    # 格式化顯示
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df['formatted_time'] = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 創建顯示用的表格
                    display_df = df[['formatted_time', 'debtor_id', 'creditor_id', 'amount']].copy()
                    display_df.columns = ['時間', '欠款人ID', '債主ID', '金額']
                    
                    st.dataframe(
                        display_df,
                        hide_index=True,
                        use_container_width=True
                    )
                    
                    # 顯示統計信息
                    st.markdown("#### 統計信息")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("總交易筆數", len(df))
                    with col2:
                        st.metric("總債務金額", f"${df['amount'].sum():,.0f}")
                    with col3:
                        st.metric("平均交易金額", f"${df['amount'].mean():,.0f}")
                    
                else:
                    st.info("📝 本月尚無交易記錄")
            else:
                st.info("📝 本月尚無交易記錄")
                
        except Exception as e:
            st.error(f"❌ 讀取債務記錄時發生錯誤：{str(e)}")
        
        # 功能說明
        st.markdown("### 💡 小提醒")
        st.info("""
        - 使用 `/debt add` 記錄新的欠款時，系統會自動處理債務互抵
        - 使用 `/debt summary` 可以隨時查看當前的債務狀況
        - 所有交易記錄都會按月份自動保存
        - 如需清除債務，請使用 `/debt clear` 命令
        """)

elif st.session_state.current_page == "設定":
    st.title("⚙️ 設定")
    
    # 機器人設定
    st.markdown("### 🤖 機器人設定")
    bot_info = st.session_state.bots[st.session_state.selected_bot]
    
    # Token 設定
    new_token = st.text_input("更新 Token", value=bot_info["token"], type="password")
    if st.button("更新 Token"):
        bot_info["token"] = new_token
        save_config()
        st.success("✅ Token 已更新")
    
    st.markdown("### 📖 使用說明")
    st.markdown("""
    1. **機器人管理** 🤖
       - 新增或移除機器人
       - 查看機器人狀態
       - 管理機器人權限
    
    2. **頻道管理** 📺
       - 新增或移除頻道
       - 設定頻道類型和功能
       - 管理頻道權限
    
    3. **節日預報** 📅
       - 設定發送時間和頻道
       - 自訂節日提醒格式
       - 管理節日資料庫
    
    4. **公告系統** 📢
       - 發送群發公告
       - 設定公告模板
       - 管理公告歷史記錄
    
    5. **安全提醒** 🔒
       - 請妥善保管機器人 Token
       - 定期更新機器人設定
       - 注意頻道權限設定
    """)
