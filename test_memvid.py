"""
Test di base per verificare la funzionalità di Memvid.
"""
import os
import sys

def main():
    print("\n===== TEST MEMVID =====\n")
    
    # Verifica l'importazione di memvid
    try:
        import memvid
        print(f"✅ Memvid importato correttamente: {memvid.__file__}")
    except ImportError as e:
        print(f"❌ Errore nell'importazione di memvid: {e}")
        print("Assicurati che memvid sia installato con: pip install memvid")
        return 1
    
    # Verifica le classi principali
    try:
        from memvid import MemvidEncoder
        print("✅ MemvidEncoder importato correttamente")
    except ImportError as e:
        print(f"❌ Errore nell'importazione di MemvidEncoder: {e}")
        return 1
    
    # Prova a creare un encoder
    try:
        encoder = MemvidEncoder()
        print("✅ MemvidEncoder inizializzato correttamente")
    except Exception as e:
        print(f"❌ Errore nell'inizializzazione di MemvidEncoder: {e}")
        return 1
    
    # Prova ad aggiungere un chunk
    try:
        encoder.add_chunks(["Questo è un test di Memvid"])
        print("✅ Aggiunta di chunk completata correttamente")
    except Exception as e:
        print(f"❌ Errore nell'aggiunta di chunk: {e}")
        return 1
    
    # Prova a creare un video (in una directory temporanea)
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_test")
    os.makedirs(temp_dir, exist_ok=True)
    
    video_path = os.path.join(temp_dir, "test.mp4")
    index_path = os.path.join(temp_dir, "test_index.json")
    
    try:
        encoder.build_video(video_path, index_path)
        print(f"✅ Video e indice creati correttamente in: {temp_dir}")
        
        # Verifica che i file siano stati creati
        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            print(f"  - Video: {os.path.getsize(video_path)} bytes")
        else:
            print("❌ Il file video non è stato creato o è vuoto")
            
        if os.path.exists(index_path) and os.path.getsize(index_path) > 0:
            print(f"  - Indice: {os.path.getsize(index_path)} bytes")
        else:
            print("❌ Il file indice non è stato creato o è vuoto")
    
    except Exception as e:
        print(f"❌ Errore nella creazione del video: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n✅ Test completato con successo!")
    print("\n=======================\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
