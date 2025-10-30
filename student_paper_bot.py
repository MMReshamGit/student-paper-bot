import os
import requests
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# Get your Telegram bot token from environment (set in Railway Variables)
BOT_TOKEN = os.getenv("8321057096:AAHClJi3S-hmrQXhGdRRJgm7cyYUHUDBc2I")

# Google Sheet JSON URL (example)
SHEET_URL = "https://opensheet.elk.sh/1LXevFkVfBGzLrBttaMPyQ-6voypCyYogQmE58JNn8w0/Sheet1"

# Optional: cache data for 5 minutes to reduce repeated fetches
cached_data = None
last_fetch_time = 0
CACHE_DURATION = 300  # seconds


def get_sheet_data():
    global cached_data, last_fetch_time
    current_time = time.time()

    # Use cached data if within cache duration
    if cached_data and current_time - last_fetch_time < CACHE_DURATION:
        return cached_data

    try:
        response = requests.get(SHEET_URL)
        if response.status_code == 200:
            cached_data = response.json()
            last_fetch_time = current_time
            return cached_data
        else:
            print("⚠️ Error fetching data:", response.status_code)
            return []
    except Exception as e:
        print("⚠️ Exception:", e)
        return []


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("GSEB", callback_data="GSEB")],
        [InlineKeyboardButton("CBSE", callback_data="CBSE")]
    ]
    await update.message.reply_text(
        "Select your Board 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Handle Board selection
async def board_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    board = query.data

    # Get live data
    data = get_sheet_data()
    standards = sorted({row["Standard"] for row in data if row["Board"] == board})

    keyboard = [[InlineKeyboardButton(std, callback_data=f"{board}|{std}")]
                for std in standards]
    await query.edit_message_text(
        text=f"Select Standard for {board}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Handle Standard selection → show subjects/papers
async def standard_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    board, std = query.data.split("|")

    data = get_sheet_data()
    filtered = [row for row in data if row["Board"] == board and row["Standard"] == std]

    if not filtered:
        await query.edit_message_text("No papers found.")
        return

    text = f"📘 Papers for {board} - Std {std}:\n\n"
    for row in filtered:
        subject = row.get("Subject", "Unknown")
        link = row.get("Link", "")
        text += f"• [{subject}]({link})\n"

    await query.edit_message_text(text, parse_mode="Markdown", disable_web_page_preview=True)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(board_selected, pattern="^(GSEB|CBSE)$"))
    app.add_handler(CallbackQueryHandler(standard_selected, pattern="^(GSEB|CBSE)\|"))
    print("✅ Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()

