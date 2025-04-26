# 📦 Database Setup

## 📊 資料庫設計概述
為了確保系統的高性能和可擴展性，我們設計了以下主要資料表：

### Bot
| 字段名稱 | 資料型態 | 說明 |
|----------|----------|------|
| id | Integer | 主鍵，自增 |
| name | String | 機器人名稱 |
| description | String | 機器人描述 |
| status | Boolean | 狀態 (啟用/停用) |
| created_at | DateTime | 創建時間 |
| updated_at | DateTime | 更新時間 |

### Server
| 字段名稱 | 資料型態 | 說明 |
|----------|----------|------|
| id | Integer | 主鍵，自增 |
| discord_id | String | Discord 伺服器 ID |
| name | String | 伺服器名稱 |
| member_count | Integer | 成員數量 |
| bot_id | Integer | 外鍵，關聯 Bot |
| created_at | DateTime | 創建時間 |
| updated_at | DateTime | 更新時間 |

### Command
| 字段名稱 | 資料型態 | 說明 |
|----------|----------|------|
| id | Integer | 主鍵，自增 |
| name | String | 指令名稱 |
| description | String | 指令描述 |
| parameters | JSON | 指令參數（JSON） |
| bot_id | Integer | 外鍵，關聯 Bot |
| created_at | DateTime | 創建時間 |
| updated_at | DateTime | 更新時間 |

### Log
| 字段名稱 | 資料型態 | 說明 |
|----------|----------|------|
| id | Integer | 主鍵，自增 |
| type | String | 錄入類型（INFO/ERROR） |
| content | Text | 日誌內容 |
| bot_id | Integer | 外鍵 |
| server_id | Integer | 外鍵 |
| created_at | DateTime | 創建時間 |

### Setting
| 字段名稱 | 資料型態 | 說明 |
|----------|----------|------|
| id | Integer | 主鍵 |
| key | String | 設定鍵 |
| value | String | 設定值 |
| bot_id | Integer | 外鍵 |
| created_at | DateTime | 創建時間 |
| updated_at | DateTime | 更新時間 |
