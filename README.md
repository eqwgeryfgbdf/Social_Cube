# Social Cube Discord Bot

一個功能豐富的 Discord 機器人，具有插件系統和網頁管理界面。

## 目前功能

### 核心功能
- ✅ Discord 機器人基本功能
- ✅ 可擴展的插件系統
- ✅ 網頁管理界面
- ✅ 插件的啟用/停用管理
- ✅ 配置保存和讀取
- ✅ 基礎測試訊息發送功能

### 管理介面
- ✅ Bot 狀態總覽
- ✅ 插件管理系統
- ✅ 使用者權限管理
- ✅ 操作記錄查看

## 開發中功能

### 1. 假期廣播功能
自動播報台灣假期資訊，支援多元化的假期來源與通知設定。

#### 主要特點：
- 🔄 台灣國定假日 API 整合（可切換其他國家）
- 📅 自訂假期管理（韓國暑假、校內活動日等）
- ⏰ 靈活的通知時間與頻率設定
  - 支援每日、每週、自訂日期通知
  - 精確到分鐘的通知時間設定
  - 可選擇是否包含例假日（六、日）
- 🌐 API 來源快速切換介面
- 📊 完整的操作記錄
  - 假期資訊更新記錄
  - API 連接狀態監控
  - 廣播執行記錄

### 2. 廣播公告功能
提供便捷的 Discord 群組公告發布系統。

#### 主要特點：
- 📢 多頻道同步廣播
  - 動態管理公告頻道（新增、刪除、修改）
  - TEST 訊息模板支援
- 👥 智慧角色標註系統
  - 自動轉換角色標註格式
  - 支援多重角色與用戶標註
- 🔒 完善的權限管理
  - 可指定發送公告的成員或角色
- 📝 詳細的發布記錄
  - 公告內容與時間戳記
  - 發送狀態追蹤
  - 異常警告系統

### 3. Discord 記帳功能
透過 Discord 指令管理借貸記錄，並提供網頁查詢介面。

#### 主要特點：
- 💰 借貸記錄管理
  - 使用 Discord 用戶 ID 作為識別
  - 支援 /debt 指令格式
  - 完整的借貸關係追蹤
- 🔍 網頁查詢介面
  - 即時借貸統計
  - 用戶 ID 對應管理
  - 資料匯出功能（CSV、JSON）
- 👤 權限管理系統
  - 角色基礎的功能限制
  - 安全性控制機制
- 📊 完整的操作記錄
  - 交易詳細資訊記錄
  - 異常操作監控

### 4. 管理介面整合
整合所有功能的統一管理平台。

#### 主要特點：
- 🎯 精簡化介面設計
  - 移除冗餘頁面
  - 保持介面清晰度
- 🔄 自動化功能
  - 每分鐘更新頻道清單
  - 即時頻道選擇功能
- ⚙️ 統一設定介面
  - 假期廣播設定
  - 公告系統配置
  - 記帳功能管理
- 📝 系統操作記錄
  - 設定變更追蹤
  - 使用者操作記錄

### 5. 視覺與互動設計
提供現代化且易用的使用者介面。

#### 主要特點：
- 🎨 視覺設計
  - 經典簡約風格
  - 高對比度配色
  - 視覺舒適度優化
- ✨ 動畫效果
  - 流暢的過渡動畫
  - 精緻的微互動設計
- 📱 使用者體驗
  - 完整的提示系統
  - 響應式設計支援
  - 直覺操作邏輯
- 📊 使用者行為分析
  - 前端效能監控
  - 互動數據收集
  - 介面優化依據

## 環境要求

- Python 3.8+
- Discord.py 2.3.2
- Django 4.2+
- 其他依賴請見 requirements.txt

## 安裝

1. 克隆專案：
```bash
git clone https://github.com/yourusername/social_cube.git
cd social_cube
```

2. 安裝依賴：
```bash
pip install -r requirements.txt
```

3. 設置環境變數：
   - 複製 `.env.example` 到 `.env`
   - 填入你的 Discord Bot Token 和其他必要設置

4. 運行數據庫遷移：
```bash
python manage.py migrate
```

5. 啟動服務：
```bash
python manage.py runserver
```

## 插件系統

### 插件結構

插件系統允許你擴展機器人的功能。每個插件都必須繼承 `BasePlugin` 類：

```python
from discord_manager.plugins import BasePlugin

class YourPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.description = "Your plugin description"
        self.version = "1.0.0"
        
    async def setup(self):
        # 初始化代碼
        pass
        
    async def cleanup(self):
        # 清理代碼
        pass
```

### 使用插件管理器

```python
from discord_manager.plugins import PluginManager

# 創建插件管理器
plugin_manager = PluginManager()

# 載入插件
await plugin_manager.load_plugin("YourPlugin")

# 啟用插件
await plugin_manager.enable_plugin("YourPlugin")

# 停用插件
await plugin_manager.disable_plugin("YourPlugin")

# 卸載插件
await plugin_manager.unload_plugin("YourPlugin")
```

### 插件配置

插件配置使用 YAML 格式保存：

```yaml
YourPlugin:
  enabled: true
  config:
    setting1: value1
    setting2: value2
```

可以通過以下方式管理配置：

```python
# 保存配置
plugin_manager.save_config("plugin_config.yml")

# 讀取配置
plugin_manager.load_config("plugin_config.yml")
```

### 創建自定義插件

1. 在 `discord_manager/plugins` 目錄下創建新的 Python 文件
2. 定義你的插件類，繼承 `BasePlugin`
3. 實現必要的方法：`setup()` 和 `cleanup()`
4. 插件會被自動發現和載入

## 開發指南

### 插件開發最佳實踐

1. **文檔完整性**
   - 提供清晰的插件描述
   - 記錄配置選項
   - 包含使用示例

2. **錯誤處理**
   - 妥善處理異常
   - 提供有意義的錯誤信息
   - 確保清理代碼在 `cleanup()` 中執行

3. **配置管理**
   - 使用 `self.config` 存儲配置
   - 提供默認值
   - 驗證配置值

4. **資源管理**
   - 在 `setup()` 中初始化資源
   - 在 `cleanup()` 中釋放資源
   - 避免資源洩漏

## 貢獻指南

1. Fork 專案
2. 創建功能分支
3. 提交更改
4. 發起 Pull Request

## 許可證

[MIT License](LICENSE)

## 聯繫方式

- 作者：[Lung Yu-Cheng]
- Email：[your.email@example.com]
- Discord：[Your Discord Tag] 