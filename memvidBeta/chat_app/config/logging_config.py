"""
Configurazione dettagliata del logging per il sistema Memvid Chat.
"""

import logging
import logging.config
from pathlib import Path
import os

# Assicura che la directory dei log esista
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

# Configurazione del logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'verbose',
            'filename': os.path.join(log_dir, 'memvid_chat.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'telegram_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'verbose',
            'filename': os.path.join(log_dir, 'telegram.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'verbose',
            'filename': os.path.join(log_dir, 'errors.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf8'
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'telegram': {
            'handlers': ['console', 'telegram_file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'telegram.ext': {
            'handlers': ['console', 'telegram_file', 'error_file'],
            'level': 'INFO',
            'propagate': False
        },
        'database': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'core': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

def setup_logging():
    """Configura il sistema di logging."""
    logging.config.dictConfig(LOGGING_CONFIG)
    logging.info("Logging configurato")

if __name__ == "__main__":
    setup_logging()
    logging.info("Test del sistema di logging")
    logging.debug("Questo è un messaggio di debug")
    logging.warning("Questo è un avviso")
    logging.error("Questo è un errore")
    try:
        raise ValueError("Errore di test")
    except Exception as e:
        logging.exception("Eccezione di test: %s", e)
