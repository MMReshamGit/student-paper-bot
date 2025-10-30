import os
import requests
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_URL = "https://opensheet.elk.sh/YOUR_SHEET_ID/Sheet1"  # Replace with your link

cached_data = None
last_fetch_time = 0
CACHE_DURATION = 300  # 5 minutes

def get_sheet_data(force_refresh=False):
    global cached_data, last_fetch_time
    current_time = time.time()

    if not force_refresh and cached_data and current_time - last_fetch_time < CACHE_DURATION:
        return cached_data

    try:
        response = requests.get(SHEET_URL)
        if response.status_code == 200:
            cached_data = response.json()
            last_fetch_time = current_time
            print("✅ Data fetched successfully.")
            return cached_data
        else:
            print(f"⚠️ Error: {response.status_code}")
            return cached_data or []
    except Exception as e:
        print("⚠️ Error:", e)
        return cached_data or []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_sheet_data()
    boards = sorted({row["Board"] for row in data if row.get("Board")})

    if not boards:
        await update.message.reply_text("⚠️ No Boards found.")
        return

    keyboard = [[InlineKeyboardButton(board, callback_data=board)] for board in boards]
    keyboard.append([InlineKeyboardButton("🔁 Refresh Data", callback_data="refresh")])

    await update.message.reply_text("📚 Select your Board 👇", reply_markup=InlineKeyboardMarkup(keyboard))

async def board_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    board = query.data

    if board == "refresh":
        get_sheet_data(force_refresh=True)
        await query.edit_message_text("🔄 Data refreshed successfully! Use /start again.")
        return

    data = get_sheet_data()
    standards = sorted({row["Standard"] for row in data if row["Board"] == board})

    if not standards:
        await query.edit_message_text(f"⚠️ No standards found for {board}.")
        return

    keyboard = [[InlineKeyboardButton(std, callback_data=f"{board}|{std}")] for std in standards]
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_boards")])

    await query.edit_message_text(
        text=f"🏫 Select Standard for *{board}:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def standard_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    board, std = query.data.split("|")

    data = get_sheet_data()
    filtered = [row for row in data if row["Board"] == board and row["Standard"] == std]

    if not filtered:
        await query.edit_message_text("⚠️ No papers found for this selection.")
        return

    text = f"📘 *Papers for {board} - Std {std}:*\n\n"
    for row in filtered:
        subject = row.get("Subject", "Unnamed Subject")
        link = row.get("Link", "")
        text += f"• [{subject}]({link})\n"

    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data=board)]]
    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(board_selected, pattern="^(?!.*\\|)(?!refresh$)(?!back_to_boards$).+"))
    app.add_handler(CallbackQueryHandler(standard_selected, pattern="^(.*)\|(.*)$"))
    app.add_handler(CallbackQueryHandler(go_back, pattern="^back_to_boards$"))
    app.add_handler(CallbackQueryHandler(board_selected, pattern="^refresh$"))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
