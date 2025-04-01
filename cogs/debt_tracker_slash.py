# cogs/debt_tracker_slash.py

import discord
from discord import app_commands
from discord.ext import commands
import logging
import csv
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DebtTrackerSlash(commands.Cog):
    """
    以 Discord Slash Command (app_commands) 形式
    實作「誰欠誰多少」的功能，並支援：
      1. 角色互換自動計算 (netting)
      2. 以 CSV 檔 (按月) 儲存交易紀錄
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # 用一個 dict 來保存當前月份的淨額資訊: debts[(debtor_id, creditor_id)] = amount
        self.debts = {}

        # 啟動時先讀取當月的 CSV，恢復淨額
        self.load_from_csv()

    @property
    def current_csv_path(self) -> Path:
        """取得當月份的 CSV 檔名，例如 data/debt/2024/debt_2024-04.csv"""
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%Y-%m")
        
        # 建立完整的資料夾路徑結構
        data_dir = Path("data")
        debt_dir = data_dir / "debt"
        year_dir = debt_dir / year
        
        # 確保所有必要的資料夾都存在
        data_dir.mkdir(exist_ok=True)
        debt_dir.mkdir(exist_ok=True)
        year_dir.mkdir(exist_ok=True)
        
        # 回傳完整的檔案路徑
        return year_dir / f"debt_{month}.csv"

    def load_from_csv(self):
        """
        讀取當月的 CSV，根據每一筆交易，重建 net。
        假設 CSV 欄位為：
          timestamp, debtor_id, creditor_id, amount
        """
        csv_file = self.current_csv_path
        if not csv_file.exists():
            logging.info(f"No CSV found for this month: {csv_file}")
            return

        try:
            with open(csv_file, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    debtor_id = int(row["debtor_id"])
                    creditor_id = int(row["creditor_id"])
                    amount = int(row["amount"])
                    self._apply_netting(debtor_id, creditor_id, amount)
            logging.info(f"Loaded existing CSV: {csv_file}")
        except Exception as e:
            logging.error(f"Failed to read {csv_file}: {e}")

    def append_to_csv(self, debtor_id: int, creditor_id: int, amount: int):
        """
        將本次交易記錄 (debtor_id, creditor_id, amount) 追加到當月 CSV。
        若檔案不存在，先寫入表頭。
        """
        csv_file = self.current_csv_path
        file_exists = csv_file.exists()

        try:
            with open(csv_file, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "debtor_id", "creditor_id", "amount"])
                if not file_exists:
                    writer.writeheader()
                writer.writerow({
                    "timestamp": datetime.now().isoformat(),
                    "debtor_id": debtor_id,
                    "creditor_id": creditor_id,
                    "amount": amount
                })
            logging.info(f"Successfully wrote to CSV: {csv_file}")
        except Exception as e:
            logging.error(f"Failed to write to {csv_file}: {e}")

    def _apply_netting(self, debtor: int, creditor: int, delta: int):
        """
        執行核心運算：
          - 先檢查有無反向紀錄 (creditor, debtor)，若存在，做互相抵銷。
          - 若差值 > 0，代表還有人欠誰；若 =0 刪除；若 <0 則角色反轉。
        """
        reverse_key = (creditor, debtor)
        reverse_amount = self.debts.get(reverse_key, 0)

        if reverse_amount > 0:
            # 有反向紀錄 => 互相抵銷
            result = reverse_amount - delta
            if result > 0:
                # 代表原本 creditor->debtor 的紀錄更大，因此抵完後仍由 creditor->debtor
                self.debts[reverse_key] = result
                # 同時 (debtor, creditor) 這筆就不需要再加
            elif result < 0:
                # 代表新加這筆比較大，抵完後剩餘由 debtor->creditor
                self.debts[reverse_key] = 0  # 原本那筆變 0
                self.debts[(debtor, creditor)] = abs(result)
            else:
                # result == 0 => 完全抵銷
                self.debts[reverse_key] = 0
        else:
            # 沒有反向紀錄 => 直接加到 (debtor, creditor)
            key = (debtor, creditor)
            old_val = self.debts.get(key, 0)
            self.debts[key] = old_val + delta

    #================= Slash Command 群組 ( /debt ) =================#

    debt_group = app_commands.Group(name="debt", description="債務相關指令")

    @app_commands.command(name="add", description="記錄一筆欠款 (某人欠某人多少錢)，並自動執行角色互換計算")
    @app_commands.describe(
        debtor="欠款人",
        creditor="被欠的人 (債主)",
        amount="欠款金額"
    )
    async def cmd_add(self, interaction: discord.Interaction,
                      debtor: discord.User,
                      creditor: discord.User,
                      amount: int):
        """
        /debt add @UserA @UserB 100
        表示 @UserA 欠 @UserB 100 元。
        當系統檢測到之前有 @UserB 欠 @UserA 的紀錄，會自動抵銷。
        """
        if amount <= 0:
            await interaction.response.send_message("金額必須大於 0！", ephemeral=True)
            return
        if debtor.id == creditor.id:
            await interaction.response.send_message("欠款人與債主不可相同！", ephemeral=True)
            return

        # 1) 執行 netting
        self._apply_netting(debtor.id, creditor.id, amount)
        # 2) 追加交易紀錄到 CSV
        self.append_to_csv(debtor.id, creditor.id, amount)

        # 3) 準備回應訊息
        response_lines = [
            f"已紀錄並計算互抵：<@{debtor.id}> 欠 <@{creditor.id}> {amount} 元。",
            "\n**更新後的債務狀況：**"
        ]

        # 4) 添加相關債務摘要
        for (d_id, c_id), amt in self.debts.items():
            if amt > 0 and (d_id == debtor.id or c_id == creditor.id):
                response_lines.append(f"<@{d_id}> 欠 <@{c_id}> **{amt}** 元")

        await interaction.response.send_message("\n".join(response_lines))

    @app_commands.command(name="summary", description="查看所有債務或特定用戶的債務狀況")
    @app_commands.describe(
        user="若指定，則查看此用戶的相關債務；若不指定，則查看所有債務"
    )
    async def cmd_summary(self, interaction: discord.Interaction, user: discord.User = None):
        """
        /debt summary [@User]
        不帶 user 時：顯示所有人的淨額債務。
        帶 user 時：只顯示跟這位用戶有關的債務。
        """
        lines = []
        if user is None:
            # 全部列出
            for (debtor_id, creditor_id), amount in self.debts.items():
                if amount > 0:
                    lines.append(f"<@{debtor_id}> 欠 <@{creditor_id}> **{amount}** 元")
        else:
            # 只列出與 user 有關的
            uid = user.id
            for (debtor_id, creditor_id), amount in self.debts.items():
                if amount <= 0:
                    continue
                if debtor_id == uid or creditor_id == uid:
                    lines.append(f"<@{debtor_id}> 欠 <@{creditor_id}> **{amount}** 元")

        if not lines:
            msg = "目前查無任何債務紀錄。"
        else:
            msg = "\n".join(lines)

        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="clear", description="清除兩位用戶之間的債務")
    @app_commands.describe(
        debtor="欠款人",
        creditor="被欠的人"
    )
    async def cmd_clear(self, interaction: discord.Interaction,
                        debtor: discord.User,
                        creditor: discord.User):
        """
        /debt clear @UserA @UserB
        清除 @UserA 欠 @UserB 的債務(歸 0)。
        (不會寫入 CSV，表示對本月狀態的直接重置。)
        """
        key = (debtor.id, creditor.id)
        old_val = self.debts.get(key, 0)
        if old_val > 0:
            self.debts[key] = 0
            await interaction.response.send_message(
                f"已清除 <@{debtor.id}> 欠 <@{creditor.id}> 的 **{old_val}** 元債務。"
            )
        else:
            await interaction.response.send_message("沒有查到該筆有效債務 (或已為 0)。", ephemeral=True)

    # 把指令掛到 /debt 底下
    debt_group.add_command(cmd_add)
    debt_group.add_command(cmd_summary)
    debt_group.add_command(cmd_clear)

    async def cog_app_command_setup(self):
        # 檢查是否已經註冊 /debt group
        if not self.bot.tree.get_command(self.debt_group.name):
            self.bot.tree.add_command(self.debt_group)

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Bot 就緒時做 Slash Command 同步。
        """
        await self.cog_app_command_setup()
        try:
            synced = await self.bot.tree.sync()
            logging.info(f"Slash commands synced: {len(synced)} commands")
        except Exception as e:
            logging.error(f"Failed to sync slash commands: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(DebtTrackerSlash(bot))
