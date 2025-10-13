"""
Script di debug per verificare la ricerca di documenti Memvid.
"""

from pathlib import Path
import sys
import os

# Determinare la directory del progetto
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importare le funzioni necessarie
from config.config import get_available_documents, MEMVID_OUTPUT_DIR

def main():
    """Funzione principale per il debug."""
    print("="*50)
    print("MEMVID CHAT DEBUG - DOCUMENT SCANNER")
    print("="*50)
    print(f"Versione Python: {sys.version}")
    print(f"Directory di esecuzione: {os.getcwd()}")
    print("="*50)
    
    # Verifica della directory di output
    output_dir = Path(MEMVID_OUTPUT_DIR)
    print(f"Directory di output configurata: {output_dir}")
    print(f"La directory esiste? {output_dir.exists()}")
    
    if output_dir.exists():
        print(f"Contenuto della directory:")
        for file in output_dir.iterdir():
            print(f"  {file.name} ({file.stat().st_size/1024:.2f} KB)")
    else:
        print("ERRORE: La directory di output non esiste!")
    
    print("="*50)
    print("Tentativo di ricerca documenti:")
    
    try:
        documents = get_available_documents()
        print(f"Documenti trovati: {len(documents)}")
        for i, doc in enumerate(documents, 1):
            print(f"{i}. ID: {doc['id']}")
            print(f"   Nome: {doc['name']}")
            print(f"   Video: {doc['video_path']}")
            print(f"   Indice: {doc['index_path']}")
            print(f"   Dimensione: {doc['size_mb']:.2f} MB")
            
            # Verifica l'esistenza dei file
            video_exists = Path(doc['video_path']).exists()
            index_exists = Path(doc['index_path']).exists()
            print(f"   File video esiste? {video_exists}")
            print(f"   File indice esiste? {index_exists}")
            
            # Se uno dei file non esiste, mostra un avviso
            if not video_exists or not index_exists:
                print(f"   ATTENZIONE: Uno o entrambi i file non esistono!")
                
    except Exception as e:
        print(f"ERRORE durante la ricerca dei documenti: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*50)
    print("DEBUG COMPLETATO")
    print("="*50)

if __name__ == "__main__":
    main()
