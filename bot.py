import discord
from discord import app_commands
from discord.ext import commands
import json
import os
from datetime import date

import os
TOKEN = os.environ["TOKEN"]

DATA_FILE = "data.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------------
# データ管理
# ------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

def get_user(uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {
            "limit": 5,
            "hearts": 0,
            "stars": 0,
            "last_report": ""
        }
    return data[uid]

# ------------------------
# Bot起動
# ------------------------

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot is ready")

# ------------------------
# /smoke
# ------------------------

@bot.tree.command(name="smoke", description="今日吸った本数を報告する")
@app_commands.describe(count="今日吸った本数")
async def smoke(interaction: discord.Interaction, count: int):
    user = get_user(interaction.user.id)

    limit = user["limit"]
    earned = max(limit - count, 0)

    user["hearts"] += earned
    user["last_report"] = str(date.today())

    star_gained = 0
    while user["hearts"] >= 10:
        user["hearts"] -= 10
        user["stars"] += 1
        star_gained += 1

    save_data(data)

    heart_display = "❤" * user["hearts"] if user["hearts"] > 0 else "なし"
    star_display = "⭐" * user["stars"] if user["stars"] > 0 else "0個"

    msg = (
        f"今日吸った本数：{count}本\n"
        f"今週の上限：{limit}本\n\n"
        f"現在のポイント！\n"
        f"{heart_display} ({user['hearts']})\n\n"
        f"ご褒美\n"
        f"{star_display}"
    )

    if star_gained > 0:
        msg += f"\n\n🎉 ご褒美（⭐）が {star_gained} 個増えた！"

    await interaction.response.send_message(msg)

# ------------------------
# ご褒美消化
# ------------------------

@bot.tree.command(name="ご褒美消化", description="ご褒美を1つ使う")
async def use_reward(interaction: discord.Interaction):
    user = get_user(interaction.user.id)

    if user["stars"] <= 0:
        await interaction.response.send_message(
            "まだご褒美はないみたい！\nまずは❤を貯めよ〜"
        )
        return

    user["stars"] -= 1
    save_data(data)

    heart_display = "❤" * user["hearts"] if user["hearts"] > 0 else "なし"

    await interaction.response.send_message(
        f"🎉 ご褒美を1つ使ったよ！\n\n"
        f"残り\n"
        f"{heart_display} ({user['hearts']})\n"
        f"⭐ {user['stars']}個"
    )

# ------------------------
# 管理者コマンドグループ
# ------------------------

admin = app_commands.Group(name="admin", description="管理者用コマンド")
bot.tree.add_command(admin)

def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

@admin.command(name="setlimit", description="上限を設定する")
async def setlimit(interaction: discord.Interaction, member: discord.Member, limit: int):
    if not is_admin(interaction):
        await interaction.response.send_message("管理者専用です", ephemeral=True)
        return

    user = get_user(member.id)
    user["limit"] = limit
    save_data(data)

    await interaction.response.send_message(
        f"🛠 上限を {limit} 本に設定しました"
    )

@admin.command(name="addheart", description="❤を追加する")
async def addheart(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not is_admin(interaction):
        await interaction.response.send_message("管理者専用です", ephemeral=True)
        return

    user = get_user(member.id)
    user["hearts"] += amount
    save_data(data)

    await interaction.response.send_message(
        f"🛠 管理者調整\n❤ +{amount}"
    )

@admin.command(name="subheart", description="❤を減らす")
async def subheart(interaction: discord.Interaction, member: discord.Member, amount: int):
    if not is_admin(interaction):
        await interaction.response.send_message("管理者専用です", ephemeral=True)
        return

    user = get_user(member.id)
    user["hearts"] = max(user["hearts"] - amount, 0)
    save_data(data)

    await interaction.response.send_message(
        f"🛠 管理者調整\n❤ -{amount}"
    )

# ------------------------
# 起動
# ------------------------

bot.run(TOKEN)
