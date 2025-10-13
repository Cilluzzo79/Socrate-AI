#!/usr/bin/env python
"""
Script per avviare l'applicazione Memvid Document Encoder.
"""
import os
import sys

def main():
    """Avvia l'applicazione web."""
    print("\n=== Avvio Memvid Document Encoder ===\n")
    
    # Verifica il percorso di esecuzione
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Directory corrente: {current_dir}")
    
    try:
        # Verifica se la cartella 'uploads' e 'outputs' esistono
        upload_dir = os.path.join(current_dir, "uploads")
        output_dir = os.path.join(current_dir, "outputs")
        
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            print(f"Creata cartella: {upload_dir}")
        else:
            print(f"Cartella esistente: {upload_dir}")
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Creata cartella: {output_dir}")
        else:
            print(f"Cartella esistente: {output_dir}")
        
        # Verifica se memvid è installato
        try:
            import memvid
            print(f"Memvid trovato: {memvid.__file__}")
        except ImportError:
            print("ERRORE: La libreria memvid non è installata o non è accessibile.")
            print("Installa tutte le dipendenze con: pip install -r requirements.txt")
            sys.exit(1)
        
        # Verifica gradio
        try:
            import gradio
            print(f"Gradio trovato: {gradio.__version__}")
        except ImportError:
            print("ERRORE: La libreria gradio non è installata.")
            print("Installa tutte le dipendenze con: pip install -r requirements.txt")
            sys.exit(1)
        
        print("\nAvvio dell'interfaccia web...")
        print("Al termine dell'avvio, apri il browser all'indirizzo: http://localhost:7860\n")
        
        # Importa e avvia l'app
        from app import app
        app.launch(server_name="0.0.0.0", server_port=7860, share=True)
    
    except ImportError as e:
        print(f"\nERRORE di importazione: {e}")
        print("Assicurati di aver installato tutte le dipendenze necessarie con:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\nERRORE durante l'avvio dell'applicazione: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
