"""
Script di debug per la funzionalità di selezione documenti nel bot Telegram.
"""

from pathlib import Path
import sys
import logging
import json

# Configura logging dettagliato
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,  # Impostato a DEBUG per ottenere più dettagli
    filename='telegram_debug.log'
)

logger = logging.getLogger(__name__)

# Determinare la directory del progetto
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importare le funzioni necessarie
from database.operations import sync_documents
from config.config import get_available_documents, MEMVID_OUTPUT_DIR

def main():
    """Funzione principale per il debug."""
    logger.info("="*50)
    logger.info("MEMVID CHAT DEBUG - TELEGRAM BOT DOCUMENT SELECTION")
    logger.info("="*50)
    
    try:
        # Verifica directory di output
        output_dir = Path(MEMVID_OUTPUT_DIR)
        logger.info(f"Directory di output configurata: {output_dir}")
        logger.info(f"La directory esiste? {output_dir.exists()}")
        
        if output_dir.exists():
            logger.info("Contenuto della directory:")
            for file in output_dir.iterdir():
                logger.info(f"  {file.name} ({file.stat().st_size/1024:.2f} KB)")
        
        # Fase 1: Ottieni documenti dalla funzione get_available_documents
        logger.info("="*50)
        logger.info("FASE 1: get_available_documents")
        available_docs = get_available_documents()
        logger.info(f"Documenti trovati: {len(available_docs)}")
        for i, doc in enumerate(available_docs):
            logger.info(f"Doc {i+1}: {doc['name']} ({doc['size_mb']:.2f} MB)")
        
        # Fase 2: Sincronizza documenti nel database
        logger.info("="*50)
        logger.info("FASE 2: sync_documents")
        try:
            db_docs = sync_documents()
            logger.info(f"Documenti sincronizzati nel DB: {len(db_docs)}")
            for i, doc in enumerate(db_docs):
                logger.info(f"DB Doc {i+1}: {doc.name} (ID: {doc.document_id})")
        except Exception as e:
            logger.error(f"Errore durante sync_documents: {e}", exc_info=True)
        
        # Fase 3: Simula creazione della tastiera inline
        logger.info("="*50)
        logger.info("FASE 3: Simulazione creazione tastiera inline")
        keyboard = []
        doc_pattern = "doc:"
        try:
            for doc in db_docs:
                button_text = f"{doc.name} ({doc.size_mb:.1f} MB)"
                callback_data = f"{doc_pattern}{doc.document_id}"
                keyboard.append([{"text": button_text, "callback_data": callback_data}])
                logger.info(f"Aggiungo bottone: {button_text} -> {callback_data}")
                # Verifica lunghezza callback_data
                if len(callback_data) > 64:
                    logger.warning(f"ATTENZIONE: callback_data troppo lungo! ({len(callback_data)} caratteri)")
            
            # Verifica JSON della tastiera
            keyboard_json = json.dumps(keyboard)
            logger.info(f"Tastiera JSON (lunghezza: {len(keyboard_json)}): {keyboard_json[:200]}{'...' if len(keyboard_json) > 200 else ''}")
        except Exception as e:
            logger.error(f"Errore durante la creazione della tastiera: {e}", exc_info=True)
        
    except Exception as e:
        logger.error(f"ERRORE GENERALE: {e}", exc_info=True)
    
    logger.info("="*50)
    logger.info("DEBUG COMPLETATO")
    logger.info("="*50)
    
    print("Debug completato. Controlla il file 'telegram_debug.log' per i risultati.")

if __name__ == "__main__":
    main()
