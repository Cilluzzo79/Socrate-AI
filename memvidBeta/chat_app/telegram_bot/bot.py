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
# Import the robust version of the pipeline
from core.rag_pipeline_robust import process_query_robust as process_query
# Import advanced handlers
from telegram_bot.advanced_handlers import (
    quiz_command, quiz_scope_selected, quiz_topic_entered, quiz_type_selected, quiz_num_selected, quiz_mode_selected, quiz_difficulty_selected, quiz_export_handler,
    outline_command, outline_scope_selected, outline_topic_input, outline_type_selected, outline_detail_selected, outline_export_handler,
    mindmap_command, mindmap_topic_selected, mindmap_topic_input, mindmap_depth_selected,
    summary_command, summary_scope_selected, summary_topic_entered, summary_type_selected, summary_export_handler,
    analyze_command, analysis_type_selected, export_analysis_handler,
    QUIZ_CONFIG, QUIZ_SCOPE, QUIZ_TOPIC, OUTLINE_CONFIG, OUTLINE_SCOPE, OUTLINE_TOPIC, OUTLINE_TYPE, MINDMAP_CONFIG, MINDMAP_TOPIC, MINDMAP_DEPTH, SUMMARY_SCOPE, SUMMARY_TOPIC, SUMMARY_CONFIG, ANALYSIS_CONFIG
)

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

# Telegram limits
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


async def send_long_message(update: Update, text: str, parse_mode: str = None):
    """
    Send a message that might exceed Telegram's character limit by splitting it into multiple messages.
    Improved version that ensures proper word boundaries.
    
    Args:
        update: The update object
        text: The text to send
        parse_mode: Optional parse mode (Markdown, HTML)
    """
    # If the message is within Telegram's limit, send it normally
    if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        await update.message.reply_text(text, parse_mode=parse_mode)
        return
    
    # Split the message into parts
    parts = []
    
    # Try to split by double newlines first (paragraphs)
    paragraphs = text.split('\n\n')
    current_part = ""
    
    for paragraph in paragraphs:
        test_part = current_part + ("\n\n" if current_part else "") + paragraph
        
        # If adding this paragraph exceeds the limit
        if len(test_part) > TELEGRAM_MAX_MESSAGE_LENGTH - 100:  # Safety margin
            # Save current part if not empty
            if current_part:
                parts.append(current_part.strip())
                current_part = ""
            
            # If the paragraph itself is too long, split it by sentences
            if len(paragraph) > TELEGRAM_MAX_MESSAGE_LENGTH - 100:
                # Split by sentences
                sentences = []
                for sep in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                    if sep in paragraph:
                        parts_temp = paragraph.split(sep)
                        sentences = [p + sep.rstrip() for p in parts_temp[:-1]] + [parts_temp[-1]]
                        break
                
                if not sentences:
                    sentences = [paragraph]
                
                for sentence in sentences:
                    test_sent = current_part + (" " if current_part else "") + sentence
                    
                    if len(test_sent) > TELEGRAM_MAX_MESSAGE_LENGTH - 100:
                        if current_part:
                            parts.append(current_part.strip())
                            current_part = ""
                        
                        # If single sentence is still too long, split by words
                        if len(sentence) > TELEGRAM_MAX_MESSAGE_LENGTH - 100:
                            words = sentence.split(' ')
                            for word in words:
                                test_word = current_part + (" " if current_part else "") + word
                                if len(test_word) > TELEGRAM_MAX_MESSAGE_LENGTH - 100:
                                    if current_part:
                                        parts.append(current_part.strip())
                                    current_part = word
                                else:
                                    current_part = test_word
                        else:
                            current_part = sentence
                    else:
                        current_part = test_sent
            else:
                current_part = paragraph
        else:
            current_part = test_part
    
    # Add the last part
    if current_part:
        parts.append(current_part.strip())
    
    # Send each part with part numbers
    for i, part in enumerate(parts):
        if len(parts) > 1:
            prefix = f"📄 Parte {i+1}/{len(parts)}\n\n"
            await update.message.reply_text(prefix + part, parse_mode=parse_mode)
        else:
            await update.message.reply_text(part, parse_mode=parse_mode)


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for cancel button in conversations."""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(text="Operazione annullata.")
    return ConversationHandler.END


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
        "🤖 *Socrate - Memvid Chat Help*\n\n"
        "Sono Socrate, il tuo assistente per l'analisi approfondita dei documenti.\n\n"
        "*📚 Comandi Base:*\n"
        "/start - Avvia il bot\n"
        "/select - Seleziona un documento\n"
        "/settings - Modifica impostazioni\n"
        "/reset - Resetta conversazione\n"
        "/help - Mostra questo messaggio\n\n"
        "*🎯 Comandi Avanzati:*\n"
        "/quiz - Genera quiz sul documento\n"
        "/outline - Crea schema/struttura\n"
        "/mindmap - Genera mappa concettuale\n"
        "/summary - Crea riassunto\n"
        "/analyze - Analisi approfondita\n\n"
        "*💡 Come usare:*\n"
        "1. Seleziona un documento con /select\n"
        "2. Fai domande o usa i comandi avanzati\n"
        "3. Riceverai risposte dettagliate e strutturate\n\n"
        "*⚙️ Funzioni Beta:*\n"
        "Usa /settings per attivare funzioni avanzate."
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
        # Process the query using the robust version
        response, metadata = process_query(
            user_id=user.id,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            user_username=user.username,
            query=message_text,
            document_id=settings.get("current_document"),
            include_history=True
        )
        
        # Send response (using the helper function for long messages)
        await send_long_message(update, response)
        
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
        logger.error(f"Error processing query: {e}", exc_info=True)
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
        elif error_type == "MessageIsTooLong":
            await update.effective_message.reply_text(
                "The response was too long to send as a single message. I'll split it into multiple parts."
            )
            # Try to split the message and send it in parts
            try:
                if hasattr(context, 'bot_data') and 'too_long_message' in context.bot_data:
                    long_message = context.bot_data['too_long_message']
                    await send_long_message(update, long_message)
                    del context.bot_data['too_long_message']
            except Exception as e:
                logger.error(f"Error sending split message: {e}")
                await update.effective_message.reply_text(
                    "I'm sorry, I couldn't send the complete response. Please try a more specific question."
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
        fallbacks=[CommandHandler('cancel', cancel_handler)]
    )
    
    settings_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('settings', settings_command)],
        states={
            ADJUSTING_SETTINGS: [
                CallbackQueryHandler(setting_selected, pattern=f"^{SETTING_PATTERN}"),
                CallbackQueryHandler(value_selected, pattern=f"^{VALUE_PATTERN}"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_handler)]
    )
    
    # Advanced conversation handlers
    quiz_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('quiz', quiz_command)],
        states={
            QUIZ_SCOPE: [
                CallbackQueryHandler(quiz_scope_selected, pattern="^quiz_scope:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$")
            ],
            QUIZ_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_topic_entered)
            ],
            QUIZ_CONFIG: [
                CallbackQueryHandler(quiz_type_selected, pattern="^quiz_type:"),
                CallbackQueryHandler(quiz_num_selected, pattern="^quiz_num:"),
                CallbackQueryHandler(quiz_mode_selected, pattern="^quiz_mode:"),
                CallbackQueryHandler(quiz_difficulty_selected, pattern="^quiz_diff:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$"),
                CallbackQueryHandler(quiz_num_selected, pattern="^back$")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_handler)]
    )
    
    outline_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('outline', outline_command)],
        states={
            OUTLINE_SCOPE: [
                CallbackQueryHandler(outline_scope_selected, pattern="^outline_scope:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$")
            ],
            OUTLINE_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, outline_topic_input)
            ],
            OUTLINE_TYPE: [
                CallbackQueryHandler(outline_type_selected, pattern="^outline_type:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$")
            ],
            OUTLINE_CONFIG: [
                CallbackQueryHandler(outline_type_selected, pattern="^outline_type:"),
                CallbackQueryHandler(outline_detail_selected, pattern="^outline_detail:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$"),
                CallbackQueryHandler(outline_command, pattern="^back$")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_handler)]
    )
    
    mindmap_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('mindmap', mindmap_command)],
        states={
            MINDMAP_TOPIC: [
                CallbackQueryHandler(mindmap_topic_selected, pattern="^mindmap_topic:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$")
            ],
            MINDMAP_DEPTH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, mindmap_topic_input)
            ],
            MINDMAP_CONFIG: [
                CallbackQueryHandler(mindmap_depth_selected, pattern="^mindmap_depth:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_handler)]
    )
    
    summary_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('summary', summary_command)],
        states={
            SUMMARY_SCOPE: [
                CallbackQueryHandler(summary_scope_selected, pattern="^summary_scope:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$")
            ],
            SUMMARY_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, summary_topic_entered)
            ],
            SUMMARY_CONFIG: [
                CallbackQueryHandler(summary_type_selected, pattern="^summary_type:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$"),
                CallbackQueryHandler(summary_command, pattern="^back$")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_handler)]
    )
    
    analysis_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('analyze', analyze_command)],
        states={
            ANALYSIS_CONFIG: [
                CallbackQueryHandler(analysis_type_selected, pattern="^analysis_type:"),
                CallbackQueryHandler(cancel_handler, pattern="^cancel$")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_handler)]
    )
    
    # Add all conversation handlers
    application.add_handler(select_conv_handler)
    application.add_handler(settings_conv_handler)
    application.add_handler(quiz_conv_handler)
    application.add_handler(outline_conv_handler)
    application.add_handler(mindmap_conv_handler)
    application.add_handler(summary_conv_handler)
    application.add_handler(analysis_conv_handler)
    
    # Register export handlers (standalone, not part of conversation)
    application.add_handler(CallbackQueryHandler(quiz_export_handler, pattern="^quiz_export:"))
    application.add_handler(CallbackQueryHandler(outline_export_handler, pattern="^outline_export:"))
    application.add_handler(CallbackQueryHandler(summary_export_handler, pattern="^summary_export:"))
    application.add_handler(CallbackQueryHandler(export_analysis_handler, pattern="^export_analysis:"))
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset", reset_command))
    
    # Register message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("Socrate Bot started with ADVANCED features. Press Ctrl+C to stop.")
    print("Available commands: /quiz, /outline, /mindmap, /summary, /analyze")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
