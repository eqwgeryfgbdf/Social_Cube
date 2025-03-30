# Social Cube Discord Bot

A Discord bot that provides holiday forecasts, announcements, and a web-based control panel for administrators.

## Project Structure

```plaintext
Social_Cube/
├─ cogs/                    # Discord bot feature modules
│  ├─ holiday_forecast.py   # Holiday forecasting and announcements
│  └─ announcement.py       # Announcement handling
├─ web/                     # Web interface components
│  └─ control_panel.py      # Streamlit-based admin panel
├─ utils/                   # Utility modules
│  └─ config.py            # Configuration and environment settings
├─ main.py                  # Main bot entry point
├─ requirements.txt         # Project dependencies
├─ .env                     # Environment variables (not in git)
├─ .env.example            # Example environment variables
└─ README.md               # This file
```

## Features

1. **Holiday Forecast**
   - Daily checks for upcoming holidays
   - Automated holiday announcements
   - Configurable announcement timing

2. **Announcement System**
   - Admin-only announcement commands
   - Direct message support for announcements
   - Channel-specific announcements

3. **Web Control Panel**
   - Streamlit-based admin interface
   - Holiday forecast management
   - Announcement creation and scheduling

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   - Copy `.env.example` to `.env`
   - Fill in your Discord bot token and channel IDs:
     ```
     DISCORD_BOT_TOKEN=your_token_here
     ANNOUNCEMENT_CHANNEL_ID=channel_id_here
     ```

3. **Start the Bot**
   ```bash
   python main.py
   ```

4. **Launch the Control Panel**
   ```bash
   streamlit run web/control_panel.py
   ```

## Dependencies

- discord.py >= 2.0.0
- python-dotenv >= 0.19.0
- streamlit >= 1.0.0
- requests >= 2.26.0

## Development

The project is structured using Discord.py's Cog system for modularity and maintainability. Each major feature is implemented as a separate Cog, making it easy to add or modify functionality.

### Adding New Features

1. Create a new Cog in the `cogs/` directory
2. Implement your feature using Discord.py's command system
3. Register the Cog in `main.py`

### Environment Variables

The bot uses environment variables for configuration. See `.env.example` for required variables and add them to your `.env` file.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

# Social Cube Discord 機器人

一個提供節日預報、公告系統和網頁控制面板的 Discord 機器人。

## 專案結構

```plaintext
Social_Cube/
├─ cogs/                    # Discord 機器人功能模組
│  ├─ holiday_forecast.py   # 節日預報和公告
│  └─ announcement.py       # 公告處理
├─ web/                     # 網頁介面元件
│  └─ control_panel.py      # 基於 Streamlit 的管理面板
├─ utils/                   # 工具模組
│  └─ config.py            # 配置和環境設定
├─ main.py                  # 機器人主入口
├─ requirements.txt         # 專案依賴
├─ .env                     # 環境變數（不在 git 中）
├─ .env.example            # 範例環境變數
└─ README.md               # 本文件
```

## 功能

1. **節日預報**
   - 每日檢查即將到來的節日
   - 自動節日公告
   - 可配置的公告時間

2. **公告系統**
   - 管理員專用公告命令
   - 支援私訊公告
   - 頻道特定公告

3. **網頁控制面板**
   - 基於 Streamlit 的管理介面
   - 節日預報管理
   - 公告創建和排程

## 安裝

1. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置環境變數**
   - 複製 `.env.example` 到 `.env`
   - 填入你的 Discord 機器人 Token 和頻道 ID：
     ```
     DISCORD_BOT_TOKEN=your_token_here
     ANNOUNCEMENT_CHANNEL_ID=channel_id_here
     ```

3. **啟動機器人**
   ```bash
   python main.py
   ```

4. **啟動控制面板**
   ```bash
   streamlit run web/control_panel.py
   ```

## 依賴

- discord.py >= 2.0.0
- python-dotenv >= 0.19.0
- streamlit >= 1.0.0
- requests >= 2.26.0

## 開發

本專案使用 Discord.py 的 Cog 系統來實現模組化和可維護性。每個主要功能都作為獨立的 Cog 實現，方便添加或修改功能。

### 添加新功能

1. 在 `cogs/` 目錄中創建新的 Cog
2. 使用 Discord.py 的命令系統實現你的功能
3. 在 `main.py` 中註冊 Cog

### 環境變數

機器人使用環境變數進行配置。請查看 `.env.example` 了解所需變數，並將它們添加到你的 `.env` 文件中。

## 貢獻

1. Fork 本倉庫
2. 創建功能分支
3. 提交你的更改
4. 推送到分支
5. 創建 Pull Request

## 授權

本專案採用 MIT 授權 - 詳見 LICENSE 文件。