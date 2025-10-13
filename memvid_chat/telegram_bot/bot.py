"""
Telegram bot handlers for the Memvid Chat system.
"""

from pathlib import Path
import sys
import logging
import json
from typing import List, Dict, Any, Optional, Union, Callable
import os

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import Telegram libraries
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes, ConversationHandler
)

# Import local modules
from config.config import TELEGRAM_BOT_TOKEN, ADMIN_USER_IDS, user_settings_manager, get_available_documents, DEBUG_MODE
from database.operations import ensure_user_exists, sync_documents, get_document_by_id
from core.rag_pipeline import process_query

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO if not DEBUG_MODE else logging.DEBUG
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_DOCUMENT = 1
ADJUSTING_SETTINGS = 2

# Callback query patterns
DOCUMENT_PATTERN = "doc:"
SETTING_PATTERN = "set:"
VALUE_PATTERN = "val:"


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /start command."""
    user = update.effective_user
    
    # Ensure user exists in database
    ensure_user_exists(
        telegram_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username
    )
    
    # Get user settings
    settings = user_settings_manager.get_user_settings(user.id)
    
    # Welcome message
    welcome_message = (
        f"👋 Welcome to Memvid Chat, {user.first_name}!\n\n"
        f"I can answer questions about documents that have been processed with Memvid.\n\n"
    )
    
    # Check if user has a current document
    if settings.get("current_document"):
        document = get_document_by_id(settings["current_document"])
        if document:
            welcome_message += f"You're currently working with document: *{document.name}*\n\n"
    else:
        welcome_message += "No document selected yet. Use /select to choose a document.\n\n"
    
    welcome_message += (
        "Available commands:\n"
        "/select - Select a document to chat with\n"
        "/settings - Adjust chat settings\n"
        "/help - Show help information\n"
        "/reset - Reset the current conversation\n\n"
        "Simply type your question to get started!"
    )
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /help command."""
    help_text = (
        "🤖 *Memvid Chat Help*\n\n"
        "This bot allows you to chat with documents that have been processed with Memvid technology.\n\n"
        "*Commands:*\n"
        "/start - Start the bot and see welcome message\n"
        "/select - Select a document to chat with\n"
        "/settings - Adjust chat settings\n"
        "/reset - Reset the current conversation\n"
        "/help - Show this help message\n\n"
        "*How to use:*\n"
        "1. Select a document using /select\n"
        "2. Ask questions about the document\n"
        "3. The bot will retrieve relevant information and answer your questions\n\n"
        "*Beta Features:*\n"
        "Use /settings to enable beta mode for advanced options."
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def select_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for /select command."""
    # Sync documents first
    try:
        documents = sync_documents()
        
        if not documents:
            await update.message.reply_text(
                "No documents found. Please make sure there are processed Memvid documents available."
            )
            return ConversationHandler.END
        
        # Create keyboard with documents
        keyboard = []
        doc_pattern = "doc:"
        for doc in documents:
            # Truncate document_id if too long (Telegram has 64-byte limit for callback_data)
            callback_id = doc.document_id
            if len(doc_pattern + callback_id) > 60:  # Leave some margin
                # Use a numeric id instead for long names
                callback_id = f"id:{doc.id}"
                logger.info(f"Using shortened callback for long document name: {doc.document_id} -> {callback_id}")
            
            # Format size with 1 decimal place
            size_text = f"{doc.size_mb:.1f} MB" if doc.size_mb >= 1 else f"{doc.size_mb*1024:.0f} KB"
            
            button = InlineKeyboardButton(
                f"{doc.name} ({size_text})",
                callback_data=f"{doc_pattern}{callback_id}"
            )
            keyboard.append([button])
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Select a document to chat with:",
            reply_markup=reply_markup
        )
        
        return SELECTING_DOCUMENT
    except Exception as e:
        logger.error(f"Error in select_document: {e}", exc_info=True)
        await update.message.reply_text(
            "An error occurred while retrieving documents. Please try again later or contact an administrator."
        )
        return ConversationHandler.END


async def document_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for document selection callback."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text(text="Document selection cancelled.")
        return ConversationHandler.END
    
    # Extract document ID
    data = query.data.replace(DOCUMENT_PATTERN, "")
    
    # Check if we're using a numeric ID
    if data.startswith("id:"):
        # Extract numeric ID
        try:
            doc_id = int(data.split(":")[1])
            # Get document from database by numeric ID
            from database.models import Document, get_session
            session = get_session()
            document = session.query(Document).filter(Document.id == doc_id).first()
            session.close()
            
            if not document:
                logger.error(f"Document with numeric ID {doc_id} not found")
                await query.edit_message_text(text="Document not found. Please try again.")
                return ConversationHandler.END
                
            # Use the document_id from the database
            document_id = document.document_id
            logger.info(f"Retrieved document by numeric ID: {doc_id} -> {document_id}")
        except Exception as e:
            logger.error(f"Error retrieving document by numeric ID: {e}", exc_info=True)
            await query.edit_message_text(text="Error retrieving document. Please try again.")
            return ConversationHandler.END
    else:
        # Use the document_id directly
        document_id = data
    
    # Get document
    document = get_document_by_id(document_id)
    if not document:
        logger.error(f"Document with ID {document_id} not found")
        await query.edit_message_text(text="Document not found. Please try again.")
        return ConversationHandler.END
    
    # Update user settings
    try:
        user_settings_manager.update_user_setting(query.from_user.id, "current_document", document_id)
        logger.info(f"User {query.from_user.id} selected document: {document_id}")
    except Exception as e:
        logger.error(f"Error updating user settings: {e}", exc_info=True)
        await query.edit_message_text(text="Error saving your selection. Please try again.")
        return ConversationHandler.END
    
    await query.edit_message_text(
        text=f"You've selected document: *{document.name}*\n\nYou can now ask questions about this document.",
        parse_mode='Markdown'
    )
    
    return ConversationHandler.END


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for /settings command."""
    user = update.effective_user
    settings = user_settings_manager.get_user_settings(user.id)
    
    # Create keyboard with settings
    keyboard = [
        [
            InlineKeyboardButton(
                f"Top K: {settings.get('top_k', 5)}",
                callback_data=f"{SETTING_PATTERN}top_k"
            )
        ],
        [
            InlineKeyboardButton(
                f"Temperature: {settings.get('temperature', 0.7)}",
                callback_data=f"{SETTING_PATTERN}temperature"
            )
        ],
        [
            InlineKeyboardButton(
                f"Max Tokens: {settings.get('max_tokens', 1500)}",
                callback_data=f"{SETTING_PATTERN}max_tokens"
            )
        ],
        [
            InlineKeyboardButton(
                f"Beta Mode: {'On' if settings.get('beta_mode', False) else 'Off'}",
                callback_data=f"{SETTING_PATTERN}beta_mode"
            )
        ],
        [
            InlineKeyboardButton("Reset to Defaults", callback_data=f"{SETTING_PATTERN}reset")
        ],
        [
            InlineKeyboardButton("Done", callback_data="cancel")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Adjust your settings:",
        reply_markup=reply_markup
    )
    
    return ADJUSTING_SETTINGS


async def setting_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for settings selection callback."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text(text="Settings adjustment cancelled.")
        return ConversationHandler.END
    
    # Extract setting
    setting = query.data.replace(SETTING_PATTERN, "")
    
    if setting == "reset":
        # Reset settings to default
        user_settings_manager.reset_user_settings(query.from_user.id)
        
        # Show updated settings
        return await show_settings(update, context)
    
    # Get current value
    settings = user_settings_manager.get_user_settings(query.from_user.id)
    current_value = settings.get(setting)
    
    # Create keyboard with values
    keyboard = []
    
    if setting == "top_k":
        options = [3, 5, 7, 10]
        for option in options:
            keyboard.append([
                InlineKeyboardButton(
                    f"{option}{' ✓' if current_value == option else ''}",
                    callback_data=f"{VALUE_PATTERN}{setting}:{option}"
                )
            ])
    
    elif setting == "temperature":
        options = [0.0, 0.3, 0.5, 0.7, 1.0]
        for option in options:
            keyboard.append([
                InlineKeyboardButton(
                    f"{option}{' ✓' if current_value == option else ''}",
                    callback_data=f"{VALUE_PATTERN}{setting}:{option}"
                )
            ])
    
    elif setting == "max_tokens":
        options = [500, 1000, 1500, 2000, 3000]
        for option in options:
            keyboard.append([
                InlineKeyboardButton(
                    f"{option}{' ✓' if current_value == option else ''}",
                    callback_data=f"{VALUE_PATTERN}{setting}:{option}"
                )
            ])
    
    elif setting == "beta_mode":
        options = [
            ("On", True),
            ("Off", False)
        ]
        for label, value in options:
            keyboard.append([
                InlineKeyboardButton(
                    f"{label}{' ✓' if current_value == value else ''}",
                    callback_data=f"{VALUE_PATTERN}{setting}:{json.dumps(value)}"
                )
            ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton("← Back", callback_data=f"{SETTING_PATTERN}back")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"Select a value for *{setting}*:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return ADJUSTING_SETTINGS


async def value_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for value selection callback."""
    query = update.callback_query
    await query.answer()
    
    # Extract setting and value
    data = query.data.replace(VALUE_PATTERN, "")
    setting, value_str = data.split(":", 1)
    
    # Parse value
    try:
        if setting == "top_k" or setting == "max_tokens":
            value = int(value_str)
        elif setting == "temperature":
            value = float(value_str)
        elif setting == "beta_mode":
            value = json.loads(value_str)
        else:
            value = value_str
    except (ValueError, json.JSONDecodeError):
        await query.edit_message_text(text=f"Invalid value for {setting}. Please try again.")
        return ConversationHandler.END
    
    # Update user settings
    user_settings_manager.update_user_setting(query.from_user.id, setting, value)
    
    # Show updated settings
    return await show_settings(update, context)


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show current settings with keyboard."""
    query = update.callback_query
    
    # Get user settings
    settings = user_settings_manager.get_user_settings(query.from_user.id)
    
    # Create keyboard with settings
    keyboard = [
        [
            InlineKeyboardButton(
                f"Top K: {settings.get('top_k', 5)}",
                callback_data=f"{SETTING_PATTERN}top_k"
            )
        ],
        [
            InlineKeyboardButton(
                f"Temperature: {settings.get('temperature', 0.7)}",
                callback_data=f"{SETTING_PATTERN}temperature"
            )
        ],
        [
            InlineKeyboardButton(
                f"Max Tokens: {settings.get('max_tokens', 1500)}",
                callback_data=f"{SETTING_PATTERN}max_tokens"
            )
        ],
        [
            InlineKeyboardButton(
                f"Beta Mode: {'On' if settings.get('beta_mode', False) else 'Off'}",
                callback_data=f"{SETTING_PATTERN}beta_mode"
            )
        ],
        [
            InlineKeyboardButton("Reset to Defaults", callback_data=f"{SETTING_PATTERN}reset")
        ],
        [
            InlineKeyboardButton("Done", callback_data="cancel")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="Adjust your settings:",
        reply_markup=reply_markup
    )
    
    return ADJUSTING_SETTINGS


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /reset command."""
    user = update.effective_user
    
    # Get user settings
    settings = user_settings_manager.get_user_settings(user.id)
    
    # Check if user has a current document
    if not settings.get("current_document"):
        await update.message.reply_text(
            "No document selected yet. Use /select to choose a document."
        )
        return
    
    # Create a new conversation (this will reset the history)
    from database.operations import get_or_create_conversation
    conversation, created = get_or_create_conversation(user.id, settings["current_document"])
    
    if created:
        await update.message.reply_text("Conversation has been reset. You can start with a new question.")
    else:
        await update.message.reply_text("Failed to reset conversation. Please try again.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages."""
    user = update.effective_user
    message_text = update.message.text
    
    # Get user settings
    settings = user_settings_manager.get_user_settings(user.id)
    
    # Check if user has a current document
    if not settings.get("current_document"):
        await update.message.reply_text(
            "No document selected yet. Use /select to choose a document."
        )
        return
    
    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        # Process the query
        response, metadata = process_query(
            user_id=user.id,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            user_username=user.username,
            query=message_text,
            document_id=settings.get("current_document"),
            include_history=True
        )
        
        # Send response
        await update.message.reply_text(response)
        
        # Show debug info in beta mode
        if settings.get("beta_mode", False) and "error" not in metadata:
            usage = metadata.get("usage", {})
            debug_message = (
                "*Debug Info:*\n"
                f"Model: `{metadata.get('model', 'N/A')}`\n"
                f"Prompt tokens: `{usage.get('prompt_tokens', 'N/A')}`\n"
                f"Completion tokens: `{usage.get('completion_tokens', 'N/A')}`\n"
                f"Total tokens: `{usage.get('total_tokens', 'N/A')}`\n"
                f"Finish reason: `{metadata.get('finish_reason', 'N/A')}`\n"
            )
            await update.message.reply_text(debug_message, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        await update.message.reply_text(
            f"I'm sorry, an error occurred while processing your question: {str(e)}"
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors with detailed information."""
    # Log the error with more details
    logger.error(f"Update {update} caused error {context.error}")
    logger.error(f"Error details: {type(context.error).__name__}: {context.error}")
    
    # Log traceback for debugging
    import traceback
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    logger.error(f"Exception traceback:\n{tb_string}")
    
    # Try to extract more info about the update
    update_info = ""
    try:
        if update:
            if update.effective_message:
                update_info += f"Message text: {update.effective_message.text}\n"
            if update.callback_query:
                update_info += f"Callback data: {update.callback_query.data}\n"
            if hasattr(update, 'effective_user') and update.effective_user:
                update_info += f"User: {update.effective_user.id} (@{update.effective_user.username})\n"
        
        logger.error(f"Additional update info:\n{update_info}")
    except Exception as e:
        logger.error(f"Error extracting update info: {e}")
    
    # Send message to user with more helpful info if possible
    if update and update.effective_message:
        error_type = type(context.error).__name__
        
        # Customize message based on error type
        if error_type == "FileNotFoundError":
            await update.effective_message.reply_text(
                "I couldn't find one of the required files. This might be because the document has been moved or deleted."
            )
        elif error_type == "DatabaseError":
            await update.effective_message.reply_text(
                "There was a problem accessing the database. Please try again later."
            )
        elif error_type == "NetworkError":
            await update.effective_message.reply_text(
                "There was a network issue while processing your request. Please check your connection and try again."
            )
        else:
            # Generic error message
            await update.effective_message.reply_text(
                f"I'm sorry, an error occurred while processing your request: {error_type}. Please try again later."
            )
        
        # If in beta mode and user is admin, send detailed error
        try:
            from config.config import ADMIN_USER_IDS, user_settings_manager
            if update.effective_user and update.effective_user.id in ADMIN_USER_IDS:
                settings = user_settings_manager.get_user_settings(update.effective_user.id)
                if settings.get("beta_mode", False):
                    error_details = str(context.error)[:200]  # Limit length
                    await update.effective_message.reply_text(
                        f"Error details (admin only):\n`{error_details}`",
                        parse_mode='Markdown'
                    )
        except Exception as e:
            logger.error(f"Failed to send admin error details: {e}")


def run_bot() -> None:
    """Run the Telegram bot."""
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register conversation handlers
    select_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('select', select_document)],
        states={
            SELECTING_DOCUMENT: [
                CallbackQueryHandler(document_selected, pattern=f"^{DOCUMENT_PATTERN}|^cancel")
            ],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    settings_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('settings', settings_command)],
        states={
            ADJUSTING_SETTINGS: [
                CallbackQueryHandler(setting_selected, pattern=f"^{SETTING_PATTERN}"),
                CallbackQueryHandler(value_selected, pattern=f"^{VALUE_PATTERN}"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern="^cancel$")
            ],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    application.add_handler(select_conv_handler)
    application.add_handler(settings_conv_handler)
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # Register message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("Bot started. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
