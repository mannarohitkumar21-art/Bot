import logging
import os
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import google.generativeai as genai

# --- CONFIGURATION ---
BOT_TOKEN = "8735856416:AAGOOQXhN-LRxQvK7UHpG4_ohIXh_FGeQow"
GEMINI_KEY = "AIzaSyDMl_EnRb4FkkgN2u5gaNhy1OlQ3S58U8Q"
ADMIN_CHAT_ID = "-1003979613521"
UPI_ID = "9735259466@fam"

# --- FIREBASE SETUP ---
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- GEMINI SETUP ---
genai.configure(api_key=GEMINI_KEY)

# --- FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    # User Database Check/Create
    user_ref = db.collection('users').document(user_id)
    if not user_ref.get().exists:
        user_ref.set({
            'username': update.effective_user.username,
            'free_video_used': False,
            'subscription': 'none'
        })

    keyboard = [
        [InlineKeyboardButton("Join Telegram", url="https://t.me/rohityt3")],
        [InlineKeyboardButton("Join WhatsApp", url="https://whatsapp.com/channel/...")],
        [InlineKeyboardButton("subcribe YouTube", url="https://youtube.com/@creatornova-j6t?si=8It3Ehf2Q5lg-q7j")],
        [InlineKeyboardButton("Submit ✅", callback_data='verify_join')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎬 Welcome to UGC Ad Maker Bot!\n\n"
        "Create AI video ads from JSON. Please join our channels to continue.",
        reply_markup=reply_markup
    )

async def handle_json(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = db.collection('users').document(user_id).get().to_dict()

    # Check Subscription or Free Trial
    if user_data['free_video_used'] and user_data['subscription'] == 'none':
        await update.message.reply_text("❌ Your free credit is over. Please buy a /plan")
        return

    try:
        json_input = update.message.text
        await update.message.reply_text("⏳ Processing your Ad Request with Gemini...")
        
        # Gemini API call (Example: Generating script or prompt)
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"Create a video ad script for this JSON: {json_input}")
        
        # Note: Actual Video Generation requires a video API (like Replicate/Luma)
        # Here we simulate sending a result
        await update.message.reply_text(f"✅ AI Script Generated:\n\n{response.text}")
        await update.message.reply_text("⚠️ [Note: Integrate a Video API to render actual MP4]")

        # Mark free video as used
        if not user_data['free_video_used']:
            db.collection('users').document(user_id).update({'free_video_used': True})

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💎 **Subscription Plans**\n\n"
        "1. Monthly: ₹30\n"
        "2. Yearly: ₹300\n\n"
        f"Pay to UPI: `{UPI_ID}`\n"
        "After payment, send the screenshot here."
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def handle_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        user = update.effective_user
        # Forward to Admin
        await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=update.message.photo[-1].file_id,
            caption=f"New Payment Request\nUser: {user.username}\nID: {user.id}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Approve Monthly", callback_data=f"approve_m_{user.id}")],
                [InlineKeyboardButton("Reject", callback_data=f"reject_{user.id}")]
            ])
        )
        await update.message.reply_text("✅ Screenshot sent to Admin. Please wait for approval.")

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("plans", show_plans))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_json))
    application.add_handler(MessageHandler(filters.PHOTO, handle_payment_screenshot))
    
    print("Bot is running...")
    application.run_polling()

