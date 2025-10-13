"""
Script veloce per rimuovere box header duplicati da Quiz, Summary e Analyze.
"""

import re
from pathlib import Path

GENERATORS_PATH = Path(__file__).parent / "content_generators.py"

def remove_duplicate_headers():
    """Remove duplicate header boxes from remaining prompts."""
    
    with open(GENERATORS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern per trovare e rimuovere i box header
    # Quiz header
    content = re.sub(
        r'\*\*Formato di Output:\*\*\n```\n# Quiz: \[Titolo descrittivo\]',
        '**Formato di Output:**\n```\n# Quiz: [Titolo descrittivo]',
        content,
        flags=re.MULTILINE
    )
    
    # Summary header  
    content = re.sub(
        r'\*\*Formato di Output:\*\*\n```\n# Riassunto: \[Titolo\]',
        '**Formato di Output:**\n```\n# Riassunto: [Titolo]',
        content,
        flags=re.MULTILINE
    )
    
    # Analysis header
    content = re.sub(
        r'\*\*Formato di Output:\*\*\n```\n# Analisi: \[Titolo\]',
        '**Formato di Output:**\n```\n# Analisi: [Titolo]',
        content,
        flags=re.MULTILINE
    )
    
    # Salva
    with open(GENERATORS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Headers rimossi da Quiz, Summary, Analyze")

if __name__ == "__main__":
    remove_duplicate_headers()
