"""
Advanced command handlers for specialized content generation.
Implements /quiz, /outline, /mindmap, /summary, and /analyze commands.
"""

from pathlib import Path
import sys
import logging
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import Telegram libraries
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Import local modules
from config.config import user_settings_manager
from core.content_generators import (
    generate_quiz_prompt,
    generate_outline_prompt,
    generate_mindmap_prompt,
    generate_summary_prompt,
    generate_analysis_prompt
)
from core.rag_pipeline_robust import process_query_robust as process_query
from utils.file_formatter import (
    format_as_txt,
    format_as_html,
    save_temp_file,
    cleanup_old_exports
)
from telegram_bot.mermaid_mindmap import (
    get_mermaid_mindmap_prompt,
    parse_simple_mindmap,
    generate_mermaid_mindmap_html
)

# Setup logging
logger = logging.getLogger(__name__)

# Conversation states for advanced commands
QUIZ_CONFIG = 100
QUIZ_SCOPE = 112
QUIZ_TOPIC = 113
OUTLINE_CONFIG = 101
OUTLINE_SCOPE = 107
OUTLINE_TOPIC = 108
OUTLINE_TYPE = 109
MINDMAP_CONFIG = 102
MINDMAP_TOPIC = 105
MINDMAP_DEPTH = 106
SUMMARY_SCOPE = 110
SUMMARY_TOPIC = 111
SUMMARY_CONFIG = 103
ANALYSIS_CONFIG = 104

# Telegram message length limit
TELEGRAM_MAX_MESSAGE_LENGTH = 4096


def get_stratified_document_chunks(document_id: str, num_chunks: int = 30) -> str:
    """
    Retrieve chunks stratified (uniformly distributed) across the entire document.
    This ensures we get a representative overview instead of semantically similar chunks.

    Args:
        document_id: ID of the document to retrieve chunks from
        num_chunks: Number of chunks to retrieve (distributed uniformly)

    Returns:
        Formatted string with document chunks
    """
    import json
    from database.operations import get_document_by_id
    from config.config import MEMVID_OUTPUT_DIR

    try:
        # Get document info
        document = get_document_by_id(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return ""

        # Load metadata file
        metadata_path = Path(MEMVID_OUTPUT_DIR) / f"{document_id}_metadata.json"
        if not metadata_path.exists():
            logger.error(f"Metadata file not found: {metadata_path}")
            return ""

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        chunks = metadata.get('chunks', [])
        total_chunks = len(chunks)

        if total_chunks == 0:
            logger.error(f"No chunks found in metadata for {document_id}")
            return ""

        # Calculate step size for uniform distribution
        step = max(1, total_chunks // num_chunks)

        # Select chunks at regular intervals
        selected_indices = [i * step for i in range(min(num_chunks, total_chunks // step))]

        # Retrieve selected chunks
        selected_chunks = []
        for idx in selected_indices:
            if idx < total_chunks:
                chunk = chunks[idx]
                text = chunk.get('text', '')
                section = chunk.get('section', idx + 1)
                total_sections = chunk.get('total_sections', total_chunks)
                page = chunk.get('page', '')
                title = chunk.get('title', '')

                # Format chunk with metadata
                chunk_header = f"[Sezione {section} di {total_sections}"
                if page:
                    chunk_header += f", Pagina {page}"
                if title:
                    chunk_header += f", {title}"
                chunk_header += "]"

                selected_chunks.append(f"{chunk_header}\n\n{text}")

        # Join all chunks
        result = "\n\n---\n\n".join(selected_chunks)
        logger.info(f"Retrieved {len(selected_chunks)} stratified chunks from {total_chunks} total chunks")

        return result

    except Exception as e:
        logger.error(f"Error retrieving stratified chunks: {e}", exc_info=True)
        return ""


def sanitize_markdown(text: str) -> str:
    """
    Sanitize text to prevent Telegram Markdown parsing errors.
    Escapes special characters that could break Markdown formatting.
    
    Args:
        text: The text to sanitize
        
    Returns:
        Sanitized text safe for Telegram Markdown
    """
    if not text:
        return text
    
    # Characters that need escaping in Telegram MarkdownV2
    # For standard Markdown (parse_mode='Markdown'), we need to escape:
    # _ * [ ] ( ) ~ ` > # + - = | { } . !
    
    # However, we want to preserve INTENTIONAL formatting
    # So we'll use a smart approach:
    
    # 1. Replace common problematic patterns
    replacements = {
        '\\': '\\\\',  # Escape backslashes first
        '_': '\\_',      # Underscore (used for italic)
        '*': '\\*',      # Asterisk (used for bold)
        '[': '\\[',      # Square brackets (used for links)
        ']': '\\]',
        '(': '\\(',      # Parentheses (used with links)
        ')': '\\)',
        '`': '\\`',      # Backtick (used for code)
        '>': '\\>',      # Greater than (used for quotes)
    }
    
    # Apply replacements
    for char, escaped in replacements.items():
        text = text.replace(char, escaped)
    
    return text


async def send_long_message(update: Update, text: str, parse_mode: str = None, context: ContextTypes.DEFAULT_TYPE = None):
    """
    Send a message that might exceed Telegram's character limit by splitting it into multiple messages.
    Automatically sanitizes text if parse_mode is Markdown to prevent parsing errors.
    """
    # Sanitize if using Markdown to prevent parsing errors
    if parse_mode == 'Markdown':
        text = sanitize_markdown(text)
        logger.debug("Text sanitized for Markdown parsing")
    
    if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        if update.message:
            await update.message.reply_text(text, parse_mode=parse_mode)
        elif update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode=parse_mode)
        return
    
    # Split the message
    parts = []
    current_part = ""
    paragraphs = text.split('\n\n')
    
    for paragraph in paragraphs:
        if len(current_part + paragraph + '\n\n') > TELEGRAM_MAX_MESSAGE_LENGTH:
            if current_part:
                parts.append(current_part.strip())
                current_part = ""
            
            if len(paragraph) > TELEGRAM_MAX_MESSAGE_LENGTH:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if len(current_part + sentence + '. ') > TELEGRAM_MAX_MESSAGE_LENGTH:
                        if current_part:
                            parts.append(current_part.strip())
                            current_part = ""
                        
                        if len(sentence) > TELEGRAM_MAX_MESSAGE_LENGTH:
                            i = 0
                            while i < len(sentence):
                                chunk_end = min(i + TELEGRAM_MAX_MESSAGE_LENGTH, len(sentence))
                                if chunk_end < len(sentence) and sentence[chunk_end] != ' ':
                                    last_space = sentence.rfind(' ', i, chunk_end)
                                    if last_space > i:
                                        chunk_end = last_space
                                parts.append(sentence[i:chunk_end].strip())
                                i = chunk_end
                        else:
                            current_part += sentence + '. '
                    else:
                        current_part += sentence + '. '
            else:
                current_part += paragraph + '\n\n'
        else:
            current_part += paragraph + '\n\n'
    
    if current_part:
        parts.append(current_part.strip())
    
    # Send each part
    for i, part in enumerate(parts):
        if len(parts) > 1:
            header = f"📄 Parte {i+1}/{len(parts)}:\n\n"
            # If adding header makes it too long, we need to re-split this part
            if len(header) + len(part) > TELEGRAM_MAX_MESSAGE_LENGTH:
                # Calculate how much content can fit with the header
                available_space = TELEGRAM_MAX_MESSAGE_LENGTH - len(header)

                # Split this oversized part into smaller chunks
                chunk_start = 0
                chunk_index = 0
                while chunk_start < len(part):
                    chunk_end = min(chunk_start + available_space, len(part))

                    # Try to break at a sentence or paragraph boundary
                    if chunk_end < len(part):
                        # Look for sentence end
                        last_period = part.rfind('. ', chunk_start, chunk_end)
                        last_newline = part.rfind('\n', chunk_start, chunk_end)
                        break_point = max(last_period, last_newline)

                        if break_point > chunk_start:
                            chunk_end = break_point + 1
                        else:
                            # Look for word boundary
                            last_space = part.rfind(' ', chunk_start, chunk_end)
                            if last_space > chunk_start:
                                chunk_end = last_space

                    chunk = part[chunk_start:chunk_end].strip()
                    chunk_header = f"📄 Parte {i+1}/{len(parts)} ({chunk_index+1}):\n\n"

                    if update.message:
                        await update.message.reply_text(chunk_header + chunk, parse_mode=parse_mode)
                    elif update.callback_query:
                        await update.callback_query.message.reply_text(chunk_header + chunk, parse_mode=parse_mode)

                    chunk_start = chunk_end
                    chunk_index += 1
            else:
                # Part fits with header, send as is
                if update.message:
                    await update.message.reply_text(header + part, parse_mode=parse_mode)
                elif update.callback_query:
                    await update.callback_query.message.reply_text(header + part, parse_mode=parse_mode)
        else:
            # Single part, no header needed
            if update.message:
                await update.message.reply_text(part, parse_mode=parse_mode)
            elif update.callback_query:
                await update.callback_query.message.reply_text(part, parse_mode=parse_mode)


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for /quiz command - start quiz generation flow."""
    user = update.effective_user
    settings = user_settings_manager.get_user_settings(user.id)

    # Check if user has a current document
    if not settings.get("current_document"):
        await update.message.reply_text(
            "❌ Nessun documento selezionato. Usa /select per scegliere un documento prima di generare un quiz."
        )
        return ConversationHandler.END

    # First ask for scope (general or topic-specific)
    keyboard = [
        [
            InlineKeyboardButton("📚 Quiz su tutto il documento", callback_data="quiz_scope:general")
        ],
        [
            InlineKeyboardButton("🎯 Quiz su tema specifico", callback_data="quiz_scope:topic")
        ],
        [
            InlineKeyboardButton("Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🎯 *Generazione Quiz*\n\n"
        "Che tipo di quiz vuoi creare?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    # Store initial configuration in context
    context.user_data['quiz_config'] = {
        'scope': None,
        'topic': None,
        'type': None,
        'num_questions': 10,
        'difficulty': 'medium',
        'focus': None
    }

    return QUIZ_SCOPE


async def quiz_scope_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle scope selection (general vs specific topic)."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione quiz annullata.")
        return ConversationHandler.END

    scope = query.data.split(":")[1]
    context.user_data['quiz_config']['scope'] = scope

    if scope == "topic":
        # Ask for topic text
        await query.edit_message_text(
            "🎯 *Quiz su Tema Specifico*\n\n"
            "Scrivi il tema o argomento su cui vuoi essere interrogato:",
            parse_mode='Markdown'
        )
        return QUIZ_TOPIC
    else:
        # General quiz - proceed to type selection
        keyboard = [
            [
                InlineKeyboardButton("📝 Scelta multipla", callback_data="quiz_type:multiple_choice"),
                InlineKeyboardButton("✓/✗ Vero/Falso", callback_data="quiz_type:true_false")
            ],
            [
                InlineKeyboardButton("✍️ Risposta breve", callback_data="quiz_type:short_answer"),
                InlineKeyboardButton("🎲 Misto", callback_data="quiz_type:mixed")
            ],
            [
                InlineKeyboardButton("← Indietro", callback_data="back"),
                InlineKeyboardButton("Annulla", callback_data="cancel")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📝 Che tipo di quiz vuoi generare?",
            reply_markup=reply_markup
        )

        return QUIZ_CONFIG


async def quiz_topic_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle topic text input for focused quiz."""
    topic = update.message.text.strip()
    context.user_data['quiz_config']['topic'] = topic

    # Now ask for quiz type
    keyboard = [
        [
            InlineKeyboardButton("📝 Scelta multipla", callback_data="quiz_type:multiple_choice"),
            InlineKeyboardButton("✓/✗ Vero/Falso", callback_data="quiz_type:true_false")
        ],
        [
            InlineKeyboardButton("✍️ Risposta breve", callback_data="quiz_type:short_answer"),
            InlineKeyboardButton("🎲 Misto", callback_data="quiz_type:mixed")
        ],
        [InlineKeyboardButton("Annulla", callback_data="cancel")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🎯 Quiz sul tema: *{topic}*\n\n"
        "📝 Che tipo di quiz vuoi generare?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return QUIZ_CONFIG


async def quiz_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quiz type selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione quiz annullata.")
        return ConversationHandler.END
    
    # Extract type
    quiz_type = query.data.split(":")[1]
    context.user_data['quiz_config']['type'] = quiz_type
    
    # Ask for number of questions
    keyboard = [
        [
            InlineKeyboardButton("5 domande", callback_data="quiz_num:5"),
            InlineKeyboardButton("10 domande", callback_data="quiz_num:10")
        ],
        [
            InlineKeyboardButton("15 domande", callback_data="quiz_num:15"),
            InlineKeyboardButton("20 domande", callback_data="quiz_num:20")
        ],
        [
            InlineKeyboardButton("← Indietro", callback_data="back"),
            InlineKeyboardButton("Annulla", callback_data="cancel")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📊 Quante domande vuoi nel quiz?",
        reply_markup=reply_markup
    )
    
    return QUIZ_CONFIG


async def quiz_num_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle number of questions selection."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione quiz annullata.")
        return ConversationHandler.END

    if query.data == "back":
        return await quiz_command(update, context)

    # Extract number
    num = int(query.data.split(":")[1])
    context.user_data['quiz_config']['num_questions'] = num

    # Ask for quiz mode (Cards vs Interactive)
    keyboard = [
        [
            InlineKeyboardButton("🎴 Card (Solo Visualizzazione)", callback_data="quiz_mode:cards")
        ],
        [
            InlineKeyboardButton("✍️ Interattivo (Con Valutazione)", callback_data="quiz_mode:interactive")
        ],
        [
            InlineKeyboardButton("← Indietro", callback_data="back"),
            InlineKeyboardButton("Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🎯 *Modalità Quiz*\n\n"
        "Scegli come vuoi visualizzare il quiz:\n\n"
        "🎴 *Card*: Domande flip interattive (clicca per vedere la risposta)\n"
        "✍️ *Interattivo*: Rispondi alle domande e ricevi una valutazione automatica",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return QUIZ_CONFIG


async def quiz_mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quiz mode selection (cards or interactive)."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione quiz annullata.")
        return ConversationHandler.END

    if query.data == "back":
        # Go back to number selection
        return await quiz_num_selected(update, context)

    # Extract mode
    mode = query.data.split(":")[1]
    context.user_data['quiz_config']['mode'] = mode

    # Ask for difficulty
    keyboard = [
        [
            InlineKeyboardButton("😊 Facile", callback_data="quiz_diff:easy"),
            InlineKeyboardButton("🤔 Medio", callback_data="quiz_diff:medium")
        ],
        [
            InlineKeyboardButton("🧠 Difficile", callback_data="quiz_diff:hard"),
            InlineKeyboardButton("🎲 Misto", callback_data="quiz_diff:mixed")
        ],
        [
            InlineKeyboardButton("← Indietro", callback_data="back"),
            InlineKeyboardButton("Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🎚️ Scegli il livello di difficoltà:",
        reply_markup=reply_markup
    )

    return QUIZ_CONFIG


async def quiz_difficulty_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle difficulty selection and generate quiz."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione quiz annullata.")
        return ConversationHandler.END
    
    if query.data == "back":
        # Go back to num selection
        return await quiz_num_selected(update, context)
    
    # Extract difficulty
    difficulty = query.data.split(":")[1]
    context.user_data['quiz_config']['difficulty'] = difficulty
    
    # Show processing message
    await query.edit_message_text(
        "⏳ Generazione del quiz in corso... Questo potrebbe richiedere alcuni secondi."
    )
    
    # Generate the quiz
    user = query.from_user
    settings = user_settings_manager.get_user_settings(user.id)
    config = context.user_data['quiz_config']

    # Create the specialized prompt
    quiz_prompt = generate_quiz_prompt(
        quiz_type=config['type'],
        num_questions=config['num_questions'],
        difficulty=config['difficulty'],
        focus_area=config.get('focus')
    )

    # Check if this is a topic-specific quiz
    if config.get('scope') == 'topic' and config.get('topic'):
        # TOPIC-SPECIFIC QUIZ: Use semantic search with focused prompt
        topic = config['topic']

        # Add focused instructions to the prompt
        focused_prompt = f"""IMPORTANTE: Genera il quiz ESCLUSIVAMENTE sul seguente argomento specifico: "{topic}"

Ignora completamente qualsiasi altro argomento o tema che non sia direttamente correlato a "{topic}".
Se il contesto include informazioni su altri argomenti, NON includerle nelle domande del quiz.

{quiz_prompt}"""

        # Temporarily increase top_k for better topic coverage
        original_top_k = settings.get("top_k", 5)
        user_settings_manager.update_user_setting(user.id, "top_k", 15)

        try:
            response, metadata = process_query(
                user_id=user.id,
                user_first_name=user.first_name,
                user_last_name=user.last_name,
                user_username=user.username,
                query=focused_prompt,
                document_id=settings.get("current_document"),
                include_history=False
            )
        except Exception as e:
            logger.error(f"Error generating topic-specific quiz: {e}")
            await query.message.reply_text(
                f"❌ Errore durante la generazione del quiz: {str(e)}"
            )
            return ConversationHandler.END
        finally:
            # Restore original top_k
            user_settings_manager.update_user_setting(user.id, "top_k", original_top_k)
    else:
        # GENERAL QUIZ: Standard process_query
        try:
            response, metadata = process_query(
                user_id=user.id,
                user_first_name=user.first_name,
                user_last_name=user.last_name,
                user_username=user.username,
                query=quiz_prompt,
                document_id=settings.get("current_document"),
                include_history=False  # Don't include history for specialized generations
            )
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            await query.message.reply_text(
                f"❌ Errore durante la generazione del quiz: {str(e)}"
            )
            return ConversationHandler.END

    # Store and send the quiz
    try:
        
        # Store the quiz for export
        import time
        context.user_data['last_quiz'] = {
            'content': response,
            'type': config['type'],
            'num_questions': config['num_questions'],
            'difficulty': config['difficulty'],
            'mode': config.get('mode', 'cards'),  # Save mode for export
            'scope': config.get('scope', 'general'),
            'topic': config.get('topic'),
            'time': time.time()
        }

        # Don't send the quiz in chat - only show download button
        # Show export button only
        export_keyboard = [
            [
                InlineKeyboardButton("🌐 Scarica Quiz Interattivo (HTML)", callback_data="quiz_export:html")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(export_keyboard)

        # Build success message with quiz info
        quiz_type_label = {
            'multiple_choice': 'Scelta Multipla',
            'true_false': 'Vero/Falso',
            'short_answer': 'Risposta Breve',
            'mixed': 'Misto'
        }.get(config['type'], config['type'])

        difficulty_label = {
            'easy': 'Facile',
            'medium': 'Medio',
            'hard': 'Difficile',
            'mixed': 'Misto'
        }.get(config['difficulty'], config['difficulty'])

        scope_label = "Generale" if config.get('scope') != 'topic' else f"Tema: {config.get('topic')}"

        await query.edit_message_text(
            f"✅ *Quiz generato con successo!*\n\n"
            f"📊 *Tipo:* {quiz_type_label}\n"
            f"🎯 *Difficoltà:* {difficulty_label}\n"
            f"📝 *Domande:* {config['num_questions']}\n"
            f"🔍 *Ambito:* {scope_label}\n\n"
            f"📥 *Scarica il quiz in formato interattivo HTML*\n"
            f"Le card permettono di cliccare sulla domanda per visualizzare la risposta!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        # Show token usage in beta mode
        if settings.get("beta_mode", False) and "error" not in metadata:
            usage = metadata.get("usage", {})
            debug_message = (
                "*📊 Statistiche Generazione:*\n"
                f"Token usati: `{usage.get('total_tokens', 'N/A')}`\n"
                f"Tempo: `{metadata.get('processing_time', 'N/A')}s`"
            )
            await query.message.reply_text(debug_message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error generating quiz: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ Si è verificato un errore durante la generazione del quiz: {str(e)}"
        )

    return ConversationHandler.END


async def outline_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for /outline command - generate document outline."""
    user = update.effective_user
    settings = user_settings_manager.get_user_settings(user.id)

    if not settings.get("current_document"):
        await update.message.reply_text(
            "❌ Nessun documento selezionato. Usa /select per scegliere un documento."
        )
        return ConversationHandler.END

    # Initialize config
    context.user_data['outline_config'] = {
        'type': None,
        'detail': 'medium',
        'scope': None,
        'topic': None
    }

    keyboard = [
        [
            InlineKeyboardButton("📖 Schema completo del documento", callback_data="outline_scope:general")
        ],
        [
            InlineKeyboardButton("🎯 Schema su tema specifico", callback_data="outline_scope:specific")
        ],
        [
            InlineKeyboardButton("❌ Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📑 *Generazione Schema*\n\n"
        "Che tipo di schema vuoi creare?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return OUTLINE_SCOPE


async def outline_scope_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle scope selection (general vs specific topic)."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione schema annullata.")
        return ConversationHandler.END

    scope = query.data.split(":")[1]
    context.user_data['outline_config']['scope'] = scope

    if scope == "general":
        # General outline - proceed to type selection
        return await show_outline_type_selection(query, context, "📖 Schema Completo del Documento")
    else:
        # Specific topic - ask for topic text
        await query.edit_message_text(
            "🎯 *Tema Specifico*\n\n"
            "Scrivi il tema o argomento su cui vuoi creare lo schema.\n\n"
            "Esempi:\n"
            "• _La Legge del Tre_\n"
            "• _I centri dell'uomo_\n"
            "• _La cosmologia esoterica_\n\n"
            "Scrivi il tema:",
            parse_mode='Markdown'
        )
        return OUTLINE_TOPIC


async def outline_topic_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user input for specific topic."""
    topic = update.message.text.strip()

    if not topic:
        await update.message.reply_text(
            "⚠️ Per favore inserisci un tema valido o usa /cancel per annullare."
        )
        return OUTLINE_TOPIC

    # Save the topic
    context.user_data['outline_config']['topic'] = topic

    # Show type selection with topic confirmed
    keyboard = [
        [
            InlineKeyboardButton("📋 Gerarchico", callback_data="outline_type:hierarchical"),
            InlineKeyboardButton("⏱️ Cronologico", callback_data="outline_type:chronological")
        ],
        [
            InlineKeyboardButton("🎯 Tematico", callback_data="outline_type:thematic")
        ],
        [
            InlineKeyboardButton("❌ Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Tema impostato: *{topic}*\n\n"
        "Ora scegli il tipo di schema:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return OUTLINE_TYPE


async def show_outline_type_selection(query, context, title="📑 Generazione Schema") -> int:
    """Show outline type selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📋 Gerarchico", callback_data="outline_type:hierarchical"),
            InlineKeyboardButton("⏱️ Cronologico", callback_data="outline_type:chronological")
        ],
        [
            InlineKeyboardButton("🎯 Tematico", callback_data="outline_type:thematic")
        ],
        [
            InlineKeyboardButton("❌ Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{title}\n\n"
        "Scegli il tipo di schema da generare:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return OUTLINE_TYPE


async def outline_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle outline type selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione schema annullata.")
        return ConversationHandler.END
    
    outline_type = query.data.split(":")[1]
    context.user_data['outline_config']['type'] = outline_type
    
    # Ask for detail level
    keyboard = [
        [
            InlineKeyboardButton("📝 Sintetico", callback_data="outline_detail:brief"),
            InlineKeyboardButton("📄 Medio", callback_data="outline_detail:medium")
        ],
        [
            InlineKeyboardButton("📚 Dettagliato", callback_data="outline_detail:detailed")
        ],
        [
            InlineKeyboardButton("← Indietro", callback_data="back"),
            InlineKeyboardButton("Annulla", callback_data="cancel")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔍 Scegli il livello di dettaglio:",
        reply_markup=reply_markup
    )
    
    return OUTLINE_CONFIG


async def outline_detail_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle detail level selection and generate outline."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione schema annullata.")
        return ConversationHandler.END
    
    if query.data == "back":
        return await outline_command(update, context)
    
    detail = query.data.split(":")[1]
    context.user_data['outline_config']['detail'] = detail
    
    # Map values to Italian for display
    type_map = {
        'hierarchical': 'Gerarchico',
        'chronological': 'Cronologico', 
        'thematic': 'Tematico'
    }
    detail_map = {
        'brief': 'Sintetico',
        'medium': 'Medio',
        'detailed': 'Dettagliato'
    }
    
    config = context.user_data['outline_config']
    type_display = type_map.get(config['type'], config['type'])
    detail_display = detail_map.get(detail, detail)
    
    # Show enhanced processing message
    processing_msg = (
        "⏳ *Generazione Schema in Corso*\n"
        "═══════════════════════════════\n\n"
        f"📋 Tipo: {type_display}\n"
        f"🔍 Dettaglio: {detail_display}\n\n"
        "⚙️ Analisi del documento...\n"
        "📝 Creazione struttura gerarchica...\n"
        "🔗 Identificazione collegamenti...\n\n"
        "_Questo potrebbe richiedere 20-40 secondi_"
    )
    await query.edit_message_text(processing_msg, parse_mode='Markdown')
    
    user = query.from_user
    settings = user_settings_manager.get_user_settings(user.id)
    
    import time
    start_time = time.time()
    
    outline_prompt = generate_outline_prompt(
        outline_type=config['type'],
        detail_level=config['detail']
    )

    try:
        # Different strategy for general vs focused outlines
        if config.get('scope') == 'general' or not config.get('topic'):
            # GENERAL outline: use stratified sampling for uniform coverage
            logger.info("Using stratified document sampling for general outline")
            document_id = settings.get("current_document")
            stratified_context = get_stratified_document_chunks(document_id, num_chunks=30)

            if not stratified_context:
                raise ValueError("Failed to retrieve stratified chunks from document")

            # Call LLM directly with stratified context
            from core.llm_client import generate_chat_response

            full_prompt = f"""Basandoti sul seguente contesto estratto dal documento, {outline_prompt}

CONTESTO DEL DOCUMENTO:
{stratified_context}

Genera ora lo schema seguendo le specifiche richieste."""

            response_data = generate_chat_response(
                query=full_prompt,
                context="",
                temperature=0.3,
                max_tokens=3000
            )
            response = response_data.get("text", "")
            metadata = {"source": "stratified_sampling"}
        else:
            # FOCUSED outline: use semantic search for specific topic
            logger.info(f"Using semantic search for topic-specific outline: {config.get('topic')}")
            original_top_k = settings.get("top_k", 5)
            settings["top_k"] = 15
            search_query = f"argomento principale del documento: {config['topic']}"

            # Add explicit instruction to focus ONLY on the requested topic
            focused_prompt = f"""IMPORTANTE: Genera lo schema ESCLUSIVAMENTE per il seguente argomento specifico: "{config['topic']}"

Ignora completamente qualsiasi altro argomento o tema che non sia direttamente correlato a "{config['topic']}".
Se il contesto include informazioni su altri argomenti, NON includerle nello schema.

{outline_prompt}

ATTENZIONE: Lo schema deve trattare SOLO "{config['topic']}" e nient'altro."""

            try:
                response, metadata = process_query(
                    user_id=user.id,
                    user_first_name=user.first_name,
                    user_last_name=user.last_name,
                    user_username=user.username,
                    query=f"{search_query}\n\n{focused_prompt}",
                    document_id=settings.get("current_document"),
                    include_history=False
                )
            finally:
                settings["top_k"] = original_top_k

        elapsed_time = time.time() - start_time

        # Store the response for export
        context.user_data['last_outline'] = {
            'content': response,
            'type': type_display,
            'detail': detail_display,
            'time': elapsed_time
        }

        # Ask for download format (no preview on chat)
        export_keyboard = [
            [
                InlineKeyboardButton("📄 Scarica TXT", callback_data="outline_export:txt"),
                InlineKeyboardButton("🌐 Scarica HTML", callback_data="outline_export:html")
            ]
        ]
        export_markup = InlineKeyboardMarkup(export_keyboard)

        success_message = (
            "✅ *Schema Generato con Successo!*\n"
            "═══════════════════════════════\n\n"
            f"📋 Tipo: {type_display}\n"
            f"🔍 Dettaglio: {detail_display}\n"
            f"⏱️ Tempo: {elapsed_time:.1f}s\n\n"
            "💾 *Scegli il formato di download:*"
        )

        await query.edit_message_text(
            success_message,
            reply_markup=export_markup,
            parse_mode='Markdown'
        )
        
        # Enhanced beta mode statistics
        if settings.get("beta_mode", False) and "error" not in metadata:
            usage = metadata.get("usage", {})
            debug_message = (
                "*📊 Statistiche Dettagliate*\n"
                "═════════════════════\n"
                f"🔢 Token totali: `{usage.get('total_tokens', 'N/A')}`\n"
                f"📥 Prompt: `{usage.get('prompt_tokens', 'N/A')}`\n"
                f"📤 Risposta: `{usage.get('completion_tokens', 'N/A')}`\n"
                f"⏱️ Generazione: `{elapsed_time:.2f}s`\n"
                f"⚡ Velocità: `{usage.get('completion_tokens', 0) / max(elapsed_time, 0.1):.1f} token/s`"
            )
            await query.message.reply_text(debug_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error generating outline: {e}", exc_info=True)
        error_msg = (
            "❌ *Errore nella Generazione*\n\n"
            f"Si è verificato un problema: {str(e)[:100]}\n\n"
            "💡 Prova a:\n"
            "• Ridurre il livello di dettaglio\n"
            "• Verificare la selezione del documento\n"
            "• Contattare il supporto se il problema persiste"
        )
        await query.message.reply_text(error_msg, parse_mode='Markdown')
    
    return ConversationHandler.END


async def mindmap_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for /mindmap command - generate mind map."""
    user = update.effective_user
    settings = user_settings_manager.get_user_settings(user.id)

    if not settings.get("current_document"):
        await update.message.reply_text(
            "❌ Nessun documento selezionato. Usa /select per scegliere un documento."
        )
        return ConversationHandler.END

    # Initialize config
    context.user_data['mindmap_config'] = {
        'depth': 3,
        'central_concept': None
    }

    keyboard = [
        [
            InlineKeyboardButton("📖 Mappa completa del documento", callback_data="mindmap_topic:general")
        ],
        [
            InlineKeyboardButton("🎯 Mappa su tema specifico", callback_data="mindmap_topic:specific")
        ],
        [
            InlineKeyboardButton("❌ Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🧠 *Generazione Mappa Mentale*\n\n"
        "Che tipo di mappa vuoi creare?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return MINDMAP_TOPIC


async def mindmap_topic_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle topic type selection."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione mappa annullata.")
        return ConversationHandler.END

    topic_type = query.data.split(":")[1]

    if topic_type == "general":
        # General map - proceed to depth selection
        context.user_data['mindmap_config']['central_concept'] = None
        return await show_depth_selection(query, context)
    else:
        # Specific topic - ask for topic text
        await query.edit_message_text(
            "🎯 *Tema Specifico*\n\n"
            "Scrivi il tema o argomento su cui vuoi creare la mappa concettuale.\n\n"
            "Esempi:\n"
            "• _La Legge del Tre_\n"
            "• _I centri dell'uomo_\n"
            "• _La cosmologia esoterica_\n\n"
            "Scrivi il tema:",
            parse_mode='Markdown'
        )
        return MINDMAP_DEPTH


async def mindmap_topic_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user input for specific topic."""
    topic = update.message.text.strip()

    if not topic:
        await update.message.reply_text(
            "⚠️ Per favore inserisci un tema valido o usa /cancel per annullare."
        )
        return MINDMAP_DEPTH

    # Save the topic
    context.user_data['mindmap_config']['central_concept'] = topic

    # Show depth selection
    keyboard = [
        [
            InlineKeyboardButton("🌿 Leggera (2 livelli)", callback_data="mindmap_depth:2"),
            InlineKeyboardButton("🌳 Media (3 livelli)", callback_data="mindmap_depth:3")
        ],
        [
            InlineKeyboardButton("🌲 Profonda (4 livelli)", callback_data="mindmap_depth:4")
        ],
        [
            InlineKeyboardButton("❌ Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"✅ Tema impostato: *{topic}*\n\n"
        "Ora scegli la profondità della mappa:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return MINDMAP_CONFIG


async def show_depth_selection(query, context) -> int:
    """Show depth selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("🌿 Leggera (2 livelli)", callback_data="mindmap_depth:2"),
            InlineKeyboardButton("🌳 Media (3 livelli)", callback_data="mindmap_depth:3")
        ],
        [
            InlineKeyboardButton("🌲 Profonda (4 livelli)", callback_data="mindmap_depth:4")
        ],
        [
            InlineKeyboardButton("❌ Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "📖 *Mappa Completa del Documento*\n\n"
        "Scegli la profondità della mappa concettuale:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return MINDMAP_CONFIG


async def mindmap_depth_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle depth selection and generate mind map."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione mappa annullata.")
        return ConversationHandler.END
    
    depth = int(query.data.split(":")[1])
    context.user_data['mindmap_config']['depth'] = depth
    
    # Map depth to display
    depth_map = {
        2: 'Leggera (2 livelli)',
        3: 'Media (3 livelli)',
        4: 'Profonda (4 livelli)'
    }
    depth_display = depth_map.get(depth, f'{depth} livelli')
    
    # Enhanced processing message
    processing_msg = (
        "⏳ *Generazione Mappa Concettuale*\n"
        "═══════════════════════════════\n\n"
        f"🌳 Profondità: {depth_display}\n\n"
        "⚙️ Identificazione concetto centrale...\n"
        "🌿 Mappatura concetti correlati...\n"
        "🔗 Analisi relazioni tra concetti...\n"
        "🎨 Creazione struttura visiva...\n\n"
        "_Questo potrebbe richiedere 15-25 secondi_"
    )
    await query.edit_message_text(processing_msg, parse_mode='Markdown')
    
    user = query.from_user
    settings = user_settings_manager.get_user_settings(user.id)
    config = context.user_data['mindmap_config']
    
    import time
    start_time = time.time()
    
    mindmap_prompt = generate_mindmap_prompt(
        central_concept=config.get('central_concept'),
        depth_level=config['depth']
    )
    
    try:
        # Use Mermaid.js template-based mindmap generation with depth level and central concept
        modified_prompt = get_mermaid_mindmap_prompt(
            depth_level=config['depth'],
            central_concept=config.get('central_concept')
        )

        # Different strategy for general vs focused mindmaps
        if config.get('central_concept'):
            # FOCUSED mindmap: use semantic search for specific concept
            original_top_k = settings.get("top_k", 5)
            settings["top_k"] = 10
            search_query = f"argomento principale del documento: {config['central_concept']}"

            try:
                response, metadata = process_query(
                    user_id=user.id,
                    user_first_name=user.first_name,
                    user_last_name=user.last_name,
                    user_username=user.username,
                    query=f"{search_query}\n\n{modified_prompt}",
                    document_id=settings.get("current_document"),
                    include_history=False
                )
            finally:
                settings["top_k"] = original_top_k
        else:
            # GENERAL mindmap: use stratified sampling for uniform coverage
            logger.info("Using stratified document sampling for general mindmap")
            document_id = settings.get("current_document")
            stratified_context = get_stratified_document_chunks(document_id, num_chunks=30)

            if not stratified_context:
                raise ValueError("Failed to retrieve stratified chunks from document")

            # Call LLM directly with stratified context
            from core.llm_client import generate_chat_response

            full_prompt = f"""Basandoti sul seguente contesto estratto dal documento, {modified_prompt}

CONTESTO DEL DOCUMENTO:
{stratified_context}

Genera ora la mappa concettuale seguendo ESATTAMENTE il formato richiesto."""

            # Generate response using LLM client
            response_data = generate_chat_response(
                query=full_prompt,
                context="",
                temperature=0.3,
                max_tokens=2000
            )
            response = response_data.get("text", "")
            metadata = {"source": "stratified_sampling"}
        
        elapsed_time = time.time() - start_time

        # Parse the simple template response
        from pathlib import Path
        mindmap_data = parse_simple_mindmap(response)

        # Generate HTML with Mermaid.js mindmap visualizer
        document_title = settings.get("current_document", "Documento")
        dashboard_html = generate_mermaid_mindmap_html(mindmap_data, document_title)

        # Save HTML file
        output_dir = Path("outputs/mindmaps")
        output_dir.mkdir(parents=True, exist_ok=True)
        html_file = output_dir / f"mindmap_{user.id}_{int(time.time())}.html"

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        # Send only success message - use HTML instead of Markdown to avoid escaping issues
        success_message = (
            "✅ <b>Mappa Concettuale Generata!</b>\n"
            "═══════════════════════════════════════\n\n"
            f"📄 Documento: {document_title}\n"
            f"🎯 Tema: {mindmap_data.get('tema_centrale', 'N/A')}\n"
            f"⏱️ Tempo: {elapsed_time:.1f}s\n"
            f"🌿 Rami: {len(mindmap_data.get('branches', []))}\n"
            f"🔗 Collegamenti: {len(mindmap_data.get('connections', []))}\n\n"
            "🚀 <b>Funzionalità:</b>\n"
            "• 🗺️ Visualizzazione interattiva ad albero\n"
            "• 🔍 Navigazione drag & zoom\n"
            "• 💡 Click sui nodi per dettagli\n"
            "• 🔗 Collegamenti tra concetti"
        )
        
        await query.edit_message_text(success_message, parse_mode='HTML')
        
        # Send HTML file
        with open(html_file, 'rb') as file:
            await query.message.reply_document(
                document=file,
                filename=f"mindmap_{document_title.replace(' ', '_').replace('/', '_')}.html",
                caption="🗺️ <b>Mappa Concettuale - Apri nel browser per visualizzare!</b>",
                parse_mode='HTML'
            )
        
        # Enhanced beta mode statistics
        if settings.get("beta_mode", False) and "error" not in metadata:
            usage = metadata.get("usage", {})
            debug_message = (
                "*📊 Statistiche Dettagliate*\n"
                "═════════════════════\n"
                f"🔢 Token totali: `{usage.get('total_tokens', 'N/A')}`\n"
                f"📥 Prompt: `{usage.get('prompt_tokens', 'N/A')}`\n"
                f"📤 Risposta: `{usage.get('completion_tokens', 'N/A')}`\n"
                f"⏱️ Generazione: `{elapsed_time:.2f}s`\n"
                f"⚡ Velocità: `{usage.get('completion_tokens', 0) / max(elapsed_time, 0.1):.1f} token/s`"
            )
            await query.message.reply_text(debug_message, parse_mode='Markdown')
        
        # Suggestions for next steps
        suggestions = (
            "\n💡 *Suggerimenti:*\n"
            "• Usa `/outline` per uno schema gerarchico dettagliato\n"
            "• Usa `/quiz` per verificare la comprensione dei concetti\n"
            "• Usa `/analyze` per un'analisi approfondita dei temi"
        )
        await query.message.reply_text(suggestions, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error generating mindmap: {e}", exc_info=True)
        error_msg = (
            "❌ *Errore nella Generazione*\n\n"
            f"Si è verificato un problema: {str(e)[:100]}\n\n"
            "💡 Prova a:\n"
            "• Ridurre la profondità della mappa\n"
            "• Verificare la selezione del documento\n"
            "• Contattare il supporto se il problema persiste"
        )
        await query.message.reply_text(error_msg, parse_mode='Markdown')
    
    return ConversationHandler.END


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for /summary command - generate summary."""
    user = update.effective_user
    settings = user_settings_manager.get_user_settings(user.id)

    if not settings.get("current_document"):
        await update.message.reply_text(
            "❌ Nessun documento selezionato. Usa /select per scegliere un documento."
        )
        return ConversationHandler.END

    # First, ask for scope (general or topic-specific)
    keyboard = [
        [
            InlineKeyboardButton("📚 Riassunto Generale", callback_data="summary_scope:general")
        ],
        [
            InlineKeyboardButton("🎯 Riassunto su Tema Specifico", callback_data="summary_scope:topic")
        ],
        [
            InlineKeyboardButton("Annulla", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📝 *Generazione Riassunto*\n\n"
        "Cosa vuoi riassumere?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    context.user_data['summary_config'] = {
        'scope': None,
        'topic': None,
        'type': None
    }

    return SUMMARY_SCOPE


async def summary_scope_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle summary scope selection (general or topic-specific)."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione riassunto annullata.")
        return ConversationHandler.END

    scope = query.data.split(":")[1]
    context.user_data['summary_config']['scope'] = scope

    if scope == "topic":
        # Ask for topic
        await query.edit_message_text(
            "🎯 *Riassunto su Tema Specifico*\n\n"
            "Scrivi il tema o argomento che vuoi riassumere:",
            parse_mode='Markdown'
        )
        return SUMMARY_TOPIC
    else:
        # General summary - proceed to type selection
        keyboard = [
            [
                InlineKeyboardButton("📄 Breve", callback_data="summary_type:brief"),
                InlineKeyboardButton("📋 Medio", callback_data="summary_type:medium")
            ],
            [
                InlineKeyboardButton("📚 Esteso", callback_data="summary_type:extended"),
                InlineKeyboardButton("📑 Per Sezioni", callback_data="summary_type:by_sections")
            ],
            [
                InlineKeyboardButton("🔙 Indietro", callback_data="back")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "📝 *Riassunto Generale*\n\n"
            "Scegli il tipo di riassunto:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        return SUMMARY_CONFIG


async def summary_topic_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle topic input for topic-specific summary."""
    topic = update.message.text.strip()

    if not topic:
        await update.message.reply_text(
            "❌ Tema non valido. Scrivi un tema o argomento specifico:"
        )
        return SUMMARY_TOPIC

    context.user_data['summary_config']['topic'] = topic

    # Now ask for summary type
    keyboard = [
        [
            InlineKeyboardButton("📄 Breve", callback_data="summary_type:brief"),
            InlineKeyboardButton("📋 Medio", callback_data="summary_type:medium")
        ],
        [
            InlineKeyboardButton("📚 Esteso", callback_data="summary_type:extended"),
            InlineKeyboardButton("📑 Per Sezioni", callback_data="summary_type:by_sections")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🎯 *Riassunto su: {topic}*\n\n"
        f"Scegli il tipo di riassunto:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return SUMMARY_CONFIG


async def summary_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle summary type selection and generate summary."""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Generazione riassunto annullata.")
        return ConversationHandler.END

    if query.data == "back":
        return await summary_command(update, context)

    summary_type = query.data.split(":")[1]
    context.user_data['summary_config']['type'] = summary_type

    await query.edit_message_text("⏳ Generazione del riassunto in corso...")

    user = query.from_user
    settings = user_settings_manager.get_user_settings(user.id)
    config = context.user_data['summary_config']

    summary_prompt = generate_summary_prompt(
        summary_type=config['type']
    )

    try:
        # Different strategy for general vs focused summaries
        if config.get('scope') == 'general' or not config.get('topic'):
            # GENERAL summary: use stratified sampling
            logger.info("Using stratified document sampling for general summary")
            document_id = settings.get("current_document")
            stratified_context = get_stratified_document_chunks(document_id, num_chunks=30)

            if not stratified_context:
                raise ValueError("Failed to retrieve stratified chunks from document")

            # Call LLM directly with stratified context
            from core.llm_client import generate_chat_response

            full_prompt = f"""Basandoti sul seguente contesto estratto dal documento, {summary_prompt}

CONTESTO DEL DOCUMENTO:
{stratified_context}

Genera ora il riassunto seguendo le specifiche richieste."""

            response_data = generate_chat_response(
                query=full_prompt,
                context="",
                temperature=0.3,
                max_tokens=3000
            )
            response = response_data.get("text", "")
            metadata = {"source": "stratified_sampling"}
        else:
            # FOCUSED summary: use semantic search for specific topic
            logger.info(f"Using semantic search for topic-specific summary: {config.get('topic')}")
            original_top_k = settings.get("top_k", 5)
            settings["top_k"] = 15
            search_query = f"argomento principale del documento: {config['topic']}"

            # Add explicit instruction to focus ONLY on the requested topic
            focused_prompt = f"""IMPORTANTE: Genera il riassunto ESCLUSIVAMENTE per il seguente argomento specifico: "{config['topic']}"

Ignora completamente qualsiasi altro argomento o tema che non sia direttamente correlato a "{config['topic']}".
Se il contesto include informazioni su altri argomenti, NON includerle nel riassunto.

{summary_prompt}

ATTENZIONE: Il riassunto deve trattare SOLO "{config['topic']}" e nient'altro."""

            try:
                response, metadata = process_query(
                    user_id=user.id,
                    user_first_name=user.first_name,
                    user_last_name=user.last_name,
                    user_username=user.username,
                    query=f"{search_query}\n\n{focused_prompt}",
                    document_id=settings.get("current_document"),
                    include_history=False
                )
            finally:
                settings["top_k"] = original_top_k

        # Store the summary for export
        import time
        context.user_data['last_summary'] = {
            'content': response,
            'type': config['type'],
            'scope': config.get('scope', 'general'),
            'topic': config.get('topic'),
            'time': time.time()
        }

        # Send the summary in chat
        await send_long_message(update, f"✅ Riassunto generato!\n\n{response}", parse_mode=None, context=context)

        # Show export buttons
        export_keyboard = [
            [
                InlineKeyboardButton("📄 Scarica TXT", callback_data="summary_export:txt"),
                InlineKeyboardButton("🌐 Scarica HTML", callback_data="summary_export:html")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(export_keyboard)
        await query.message.reply_text(
            "📥 *Scarica il riassunto*\n\nScegli il formato di esportazione:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        if settings.get("beta_mode", False) and "error" not in metadata:
            usage = metadata.get("usage", {})
            debug_message = f"*📊 Token usati:* `{usage.get('total_tokens', 'N/A')}`"
            await query.message.reply_text(debug_message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        await query.message.reply_text(f"❌ Errore: {str(e)}")

    return ConversationHandler.END


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handler for /analyze command - perform deep analysis."""
    user = update.effective_user
    settings = user_settings_manager.get_user_settings(user.id)
    
    if not settings.get("current_document"):
        await update.message.reply_text(
            "❌ Nessun documento selezionato. Usa /select per scegliere un documento."
        )
        return ConversationHandler.END
    
    keyboard = [
        [
            InlineKeyboardButton("🎨 Tematica", callback_data="analysis_type:thematic"),
            InlineKeyboardButton("💭 Argomentativa", callback_data="analysis_type:argumentative")
        ],
        [
            InlineKeyboardButton("🔍 Critica", callback_data="analysis_type:critical"),
            InlineKeyboardButton("⚖️ Comparativa", callback_data="analysis_type:comparative")
        ],
        [
            InlineKeyboardButton("🌐 Contestuale", callback_data="analysis_type:contextual")
        ],
        [
            InlineKeyboardButton("Annulla", callback_data="cancel")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔬 *Analisi Approfondita*\n\n"
        "Scegli il tipo di analisi da effettuare:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    context.user_data['analysis_config'] = {
        'type': None,
        'depth': 'profonda'
    }
    
    return ANALYSIS_CONFIG


async def outline_export_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle outline export button clicks."""
    query = update.callback_query
    await query.answer()
    
    export_type = query.data.split(":")[1]
    
    # Get stored outline
    outline_data = context.user_data.get('last_outline')
    if not outline_data:
        await query.edit_message_text("❌ Errore: Schema non trovato. Genera un nuovo schema con /outline")
        return
    
    user = query.from_user
    settings = user_settings_manager.get_user_settings(user.id)
    doc_name = settings.get("current_document", "Documento")
    
    try:
        if export_type in ["txt", "html"]:
            await query.edit_message_text("⏳ Preparazione file...")
            
            # Prepare metadata
            metadata = {
                'Documento': doc_name,
                'Tipo': outline_data['type'],
                'Dettaglio': outline_data['detail'],
                'Tempo generazione': f"{outline_data['time']:.1f}s"
            }
            
            # Generate and send file
            if export_type == "txt":
                # Generate TXT
                txt_content = format_as_txt(
                    content=outline_data['content'],
                    title=f"SCHEMA - {doc_name}",
                    metadata=metadata
                )
                txt_path = save_temp_file(txt_content, f"schema_{doc_name}", "txt")

                # Send TXT file
                with open(txt_path, 'rb') as f:
                    await query.message.reply_document(
                        document=f,
                        filename=f"schema_{doc_name}.txt",
                        caption="📄 *Schema in formato TXT*\n\nFile di testo semplice, leggibile ovunque!",
                        parse_mode='Markdown'
                    )

                await query.edit_message_text("✅ File TXT inviato con successo!")

            elif export_type == "html":
                # Generate professional interactive HTML (simple, no parsing required)
                from telegram_bot.outline_visualizer_simple import generate_simple_outline_html

                # Get outline type and detail level labels
                outline_type_label = {
                    'hierarchical': 'Gerarchico',
                    'chronological': 'Cronologico',
                    'thematic': 'Tematico',
                    'conceptual': 'Concettuale'
                }.get(outline_data['type'], outline_data['type'])

                detail_label = {
                    'brief': 'Essenziale',
                    'medium': 'Medio',
                    'detailed': 'Dettagliato'
                }.get(outline_data['detail'], outline_data['detail'])

                # Generate interactive HTML directly from text (no parsing)
                html_content = generate_simple_outline_html(
                    outline_text=outline_data['content'],
                    document_title=doc_name,
                    outline_type=outline_type_label,
                    detail_level=detail_label
                )

                html_path = save_temp_file(html_content, f"schema_{doc_name}", "html")

                # Send HTML file
                with open(html_path, 'rb') as f:
                    await query.message.reply_document(
                        document=f,
                        filename=f"schema_{doc_name}.html",
                        caption="🌐 *Schema Interattivo HTML*\n\nApri con il browser per una visualizzazione professionale e accattivante!",
                        parse_mode='Markdown'
                    )

                await query.edit_message_text("✅ File HTML inviato con successo!")

            # Cleanup old exports
            cleanup_old_exports()

    except Exception as e:
        logger.error(f"Error exporting outline: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ Errore durante l'esportazione: {str(e)[:100]}\n\n"
            "Riprova o contatta il supporto."
        )


async def summary_export_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle summary export button clicks."""
    query = update.callback_query
    await query.answer()

    export_type = query.data.split(":")[1]

    # Get stored summary
    summary_data = context.user_data.get('last_summary')
    if not summary_data:
        await query.edit_message_text("❌ Errore: Riassunto non trovato. Genera un nuovo riassunto con /summary")
        return

    user = query.from_user
    settings = user_settings_manager.get_user_settings(user.id)
    doc_name = settings.get("current_document", "Documento")

    try:
        await query.edit_message_text("⏳ Preparazione file...")

        # Prepare metadata
        summary_type_label = {
            'brief': 'Breve',
            'medium': 'Medio',
            'extended': 'Esteso',
            'by_sections': 'Per Sezioni'
        }.get(summary_data['type'], summary_data['type'])

        scope_label = {
            'general': 'Generale',
            'topic': f"Tema: {summary_data.get('topic', 'N/A')}"
        }.get(summary_data.get('scope', 'general'), 'Generale')

        metadata = {
            'Documento': doc_name,
            'Tipo': summary_type_label,
            'Ambito': scope_label
        }

        # Generate and send file
        if export_type == "txt":
            # Generate TXT
            txt_content = format_as_txt(
                content=summary_data['content'],
                title=f"RIASSUNTO - {doc_name}",
                metadata=metadata
            )
            txt_path = save_temp_file(txt_content, f"riassunto_{doc_name}", "txt")

            # Send TXT file
            with open(txt_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=f"riassunto_{doc_name}.txt",
                    caption="📄 *Riassunto in formato TXT*\n\nFile di testo semplice, leggibile ovunque!",
                    parse_mode='Markdown'
                )

            await query.edit_message_text("✅ File TXT inviato con successo!")

        elif export_type == "html":
            # Generate HTML using format_as_html
            html_content = format_as_html(
                content=summary_data['content'],
                title=f"RIASSUNTO - {doc_name}",
                metadata=metadata
            )

            html_path = save_temp_file(html_content, f"riassunto_{doc_name}", "html")

            # Send HTML file
            with open(html_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=f"riassunto_{doc_name}.html",
                    caption="🌐 *Riassunto in formato HTML*\n\nApri con il browser per una visualizzazione professionale!",
                    parse_mode='Markdown'
                )

            await query.edit_message_text("✅ File HTML inviato con successo!")

        # Cleanup old exports
        cleanup_old_exports()

    except Exception as e:
        logger.error(f"Error exporting summary: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ Errore durante l'esportazione: {str(e)[:100]}\n\n"
            "Riprova o contatta il supporto."
        )


async def quiz_export_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quiz export button clicks."""
    query = update.callback_query
    await query.answer()

    export_type = query.data.split(":")[1]

    # Get stored quiz
    quiz_data = context.user_data.get('last_quiz')
    if not quiz_data:
        await query.edit_message_text("❌ Errore: Quiz non trovato. Genera un nuovo quiz con /quiz")
        return

    user = query.from_user
    settings = user_settings_manager.get_user_settings(user.id)
    doc_name = settings.get("current_document", "Documento")

    try:
        await query.edit_message_text("⏳ Generazione quiz...")

        # Determine which HTML generator to use based on mode
        quiz_mode = quiz_data.get('mode', 'cards')  # default to cards for backward compatibility

        if quiz_mode == 'interactive':
            # Generate interactive quiz with grading
            from telegram_bot.quiz_interactive import generate_interactive_quiz_html

            html_content = generate_interactive_quiz_html(
                quiz_content=quiz_data['content'],
                document_title=doc_name,
                quiz_config={
                    'type': quiz_data['type'],
                    'difficulty': quiz_data['difficulty'],
                    'num_questions': quiz_data['num_questions']
                },
                logo_path=None
            )

            caption = ("✍️ *Quiz Interattivo con Valutazione*\n\n"
                      "Apri il file HTML con il browser, rispondi alle domande e clicca 'Valuta' per vedere il tuo punteggio!\n\n"
                      "✨ Caratteristiche:\n"
                      "• Campi di input per le risposte\n"
                      "• Valutazione automatica\n"
                      "• Feedback immediato\n"
                      "• Mostra risposte corrette")

        else:  # cards mode
            # Generate interactive HTML with flip cards
            from telegram_bot.quiz_cards import generate_quiz_cards_html

            html_content = generate_quiz_cards_html(
                quiz_content=quiz_data['content'],
                document_title=doc_name,
                quiz_config={
                    'type': quiz_data['type'],
                    'difficulty': quiz_data['difficulty'],
                    'num_questions': quiz_data['num_questions']
                },
                logo_path=None
            )

            caption = ("🎴 *Quiz Interattivo con Card*\n\n"
                      "Apri il file HTML con il browser e clicca su ogni card per visualizzare le risposte!\n\n"
                      "✨ Caratteristiche:\n"
                      "• Card interattive con animazione flip\n"
                      "• Design moderno e accattivante\n"
                      "• Stampabile o esportabile in PDF")

        html_path = save_temp_file(html_content, f"quiz_{doc_name}", "html")

        # Send HTML file
        with open(html_path, 'rb') as f:
            await query.message.reply_document(
                document=f,
                filename=f"quiz_{doc_name}.html",
                caption=caption,
                parse_mode='Markdown'
            )

        await query.edit_message_text("✅ Quiz inviato con successo!")

        # Cleanup old exports
        cleanup_old_exports()

    except Exception as e:
        logger.error(f"Error exporting quiz: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ Errore durante l'esportazione: {str(e)[:100]}\n\n"
            "Riprova o contatta il supporto."
        )


async def analysis_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle analysis type selection and perform analysis."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel":
        await query.edit_message_text("❌ Analisi annullata.")
        return ConversationHandler.END
    
    analysis_type = query.data.split(":")[1]
    context.user_data['analysis_config']['type'] = analysis_type
    
    await query.edit_message_text("⏳ Analisi in corso... Questo potrebbe richiedere un po' di tempo.")
    
    user = query.from_user
    settings = user_settings_manager.get_user_settings(user.id)
    config = context.user_data['analysis_config']
    
    analysis_prompt = generate_analysis_prompt(
        analysis_type=config['type'],
        depth=config.get('depth', 'profonda')
    )
    
    try:
        response, metadata = process_query(
            user_id=user.id,
            user_first_name=user.first_name,
            user_last_name=user.last_name,
            user_username=user.username,
            query=analysis_prompt,
            document_id=settings.get("current_document"),
            include_history=False
        )

        # Store analysis data for export
        context.user_data['last_analysis'] = {
            'content': response,
            'type': config['type'],
            'depth': config.get('depth', 'profonda'),
            'document_id': settings.get("current_document")
        }

        # Don't use Markdown to avoid parsing errors
        await send_long_message(update, f"✅ Analisi completata!\n\n{response}", parse_mode=None, context=context)

        # Show download buttons
        keyboard = [
            [
                InlineKeyboardButton("📄 Scarica TXT", callback_data="export_analysis:txt"),
                InlineKeyboardButton("🌐 Scarica HTML", callback_data="export_analysis:html")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            "💾 *Esporta l'analisi*\n\nScegli il formato di download:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        if settings.get("beta_mode", False) and "error" not in metadata:
            usage = metadata.get("usage", {})
            debug_message = f"*📊 Token usati:* `{usage.get('total_tokens', 'N/A')}`"
            await query.message.reply_text(debug_message, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error performing analysis: {e}", exc_info=True)
        await query.message.reply_text(f"❌ Errore: {str(e)}")

    return ConversationHandler.END


async def export_analysis_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle analysis export in TXT or HTML format."""
    query = update.callback_query
    await query.answer()

    if 'last_analysis' not in context.user_data:
        await query.edit_message_text("❌ Nessuna analisi disponibile per l'esportazione.")
        return

    try:
        analysis_data = context.user_data['last_analysis']
        content = analysis_data['content']
        analysis_type = analysis_data['type']

        # Get document name
        doc_manager = DocumentManager()
        doc_id = analysis_data.get('document_id')
        doc_name = "documento"
        if doc_id:
            docs = doc_manager.get_documents()
            for doc in docs:
                if doc['document_id'] == doc_id:
                    doc_name = doc['name'].replace('_sections', '')
                    break

        export_format = query.data.split(":")[1]

        # Map analysis type to display name
        type_map = {
            "thematic": "Tematica",
            "argumentative": "Argomentativa",
            "critical": "Critica",
            "comparative": "Comparativa",
            "contextual": "Contestuale"
        }
        type_display = type_map.get(analysis_type, analysis_type)

        if export_format == "txt":
            # Export as TXT with markdown formatting
            txt_content = format_as_txt(
                content=content,
                title=f"Analisi {type_display}: {doc_name}",
                metadata={
                    'Tipo': type_display,
                    'Profondità': analysis_data.get('depth', 'profonda'),
                    'Documento': doc_name
                }
            )

            file_path = save_temp_file(txt_content, f"analisi_{doc_name}", "txt")

            with open(file_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=f"analisi_{doc_name}.txt",
                    caption=f"📄 *Analisi {type_display}*\n\nFormato: Markdown (TXT)",
                    parse_mode='Markdown'
                )

        elif export_format == "html":
            # Export as HTML using the same template as other tools
            html_content = format_as_html(
                content=content,
                title=f"Analisi {type_display}: {doc_name}",
                metadata={
                    'Tipo': type_display,
                    'Profondità': analysis_data.get('depth', 'profonda'),
                    'Documento': doc_name
                }
            )

            file_path = save_temp_file(html_content, f"analisi_{doc_name}", "html")

            with open(file_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=f"analisi_{doc_name}.html",
                    caption=f"🌐 *Analisi {type_display}*\n\nApri con un browser per visualizzare l'analisi con design professionale!",
                    parse_mode='Markdown'
                )

        await query.edit_message_text("✅ Analisi esportata con successo!")

        # Cleanup old exports
        cleanup_old_exports()

    except Exception as e:
        logger.error(f"Error exporting analysis: {e}", exc_info=True)
        await query.message.reply_text(
            f"❌ Errore durante l'esportazione: {str(e)[:100]}\n\n"
            "Riprova o contatta il supporto."
        )
