"""
Esempio di utilizzo base di Memvid senza interfaccia grafica.
Questo script codifica il file test_document.md in un video Memvid.
"""
import os
import sys

def main():
    try:
        print("\n=== Esempio Base di Memvid ===\n")
        
        # Importa Memvid
        try:
            from memvid import MemvidEncoder
        except ImportError as e:
            print(f"ERRORE: {e}")
            print("Assicurati che memvid sia installato con: pip install memvid")
            return 1
            
        # Percorsi dei file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(base_dir, "test_document.md")
        output_dir = os.path.join(base_dir, "outputs")
        
        # Verifica che il file di test esista
        if not os.path.exists(test_file):
            print(f"ERRORE: File di test non trovato: {test_file}")
            return 1
            
        # Crea la directory di output se non esiste
        os.makedirs(output_dir, exist_ok=True)
        
        # Nomi dei file di output
        output_video = os.path.join(output_dir, "esempio_base.mp4")
        output_index = os.path.join(output_dir, "esempio_base_index.json")
        
        print(f"File di input: {test_file}")
        print(f"File video di output: {output_video}")
        print(f"File indice di output: {output_index}")
        
        # Leggi il contenuto del file di test
        with open(test_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        print(f"\nContenuto letto: {len(content)} caratteri")
        
        # Crea l'encoder
        encoder = MemvidEncoder()
        
        # Parametri di chunking
        chunk_size = 500
        overlap = 50
        
        print(f"Utilizzo di chunk_size={chunk_size}, overlap={overlap}")
        
        # Invece di suddividere manualmente il testo, passiamo i parametri a add_text
        encoder.add_text(content, chunk_size=chunk_size, overlap=overlap)
        
        # Costruisci il video
        print("\nGenerazione del video in corso...")
        encoder.build_video(output_video, output_index)
        
        # Verifica i file generati
        if os.path.exists(output_video):
            print(f"Video creato con successo: {os.path.getsize(output_video) / 1024:.2f} KB")
        else:
            print("ERRORE: Il video non è stato creato")
            
        if os.path.exists(output_index):
            print(f"Indice creato con successo: {os.path.getsize(output_index) / 1024:.2f} KB")
        else:
            print("ERRORE: L'indice non è stato creato")
            
        print("\nProcesso completato con successo!")
        return 0
            
    except Exception as e:
        import traceback
        print(f"\nERRORE: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
