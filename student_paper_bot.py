from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import requests

# === REPLACE THESE TWO VALUES ===
TOKEN = "8321057096:AAHClJi3S-hmrQXhGdRRJgm7cyYUHUDBc2I"
JSON_URL = "https://opensheet.elk.sh/1LXevFkVfBGzLrBttaMPyQ-6voypCyYogQmE58JNn8w0/Sheet1"

# Load data from Google Sheet JSON
def load_data():
    response = requests.get(JSON_URL)
    return response.json()

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("GSEB", callback_data='board_GSEB')],
        [InlineKeyboardButton("CBSE", callback_data='board_CBSE')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📘 Please select your Board:", reply_markup=reply_markup)

# Handle Board Selection
async def board_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    board = query.data.split('_')[1]
    context.user_data['board'] = board

    data = load_data()
    standards = sorted(set([row['Standard'] for row in data if row['Board'] == board]))
    keyboard = [[InlineKeyboardButton(std, callback_data=f'std_{std}')] for std in standards]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"✅ You selected *{board}*\n\nNow select your Standard:",
                                  reply_markup=reply_markup, parse_mode="Markdown")

# Handle Standard Selection
async def standard_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    standard = query.data.split('_')[1]
    board = context.user_data['board']
    context.user_data['standard'] = standard

    data = load_data()
    subjects = sorted(set([row['Subject'] for row in data if row['Board'] == board and row['Standard'] == standard]))
    keyboard = [[InlineKeyboardButton(sub, callback_data=f'sub_{sub}')] for sub in subjects]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"📚 You selected *{board} - Std {standard}*\nSelect a subject:",
                                  reply_markup=reply_markup, parse_mode="Markdown")

# Handle Subject Selection
async def subject_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    subject = query.data.split('_', 1)[1]
    board = context.user_data['board']
    standard = context.user_data['standard']

    data = load_data()
    papers = [row for row in data if row['Board'] == board and row['Standard'] == standard and row['Subject'] == subject]

    keyboard = [
        [InlineKeyboardButton(row['PaperName'], url=row['Link'])] for row in papers
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"📝 Papers for *{subject} ({board} Std {standard})*:",
                                  reply_markup=reply_markup, parse_mode="Markdown")

# Run the Bot
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(board_selection, pattern='^board_'))
    app.add_handler(CallbackQueryHandler(standard_selection, pattern='^std_'))
    app.add_handler(CallbackQueryHandler(subject_selection, pattern='^sub_'))
    app.run_polling()

if __name__ == "__main__":
    main()
