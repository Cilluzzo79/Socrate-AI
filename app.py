"""
Memvid PDF and Text Encoder App
--------------------------------
A web interface for encoding documents into Memvid QR video format.
"""
import os
import sys
import gradio as gr
try:
    from memvid import MemvidEncoder
except ImportError:
    print("Errore: La libreria memvid non è installata o non è accessibile.")
    print("Assicurati di aver installato tutte le dipendenze con: pip install -r requirements.txt")
    sys.exit(1)

# Configurazione delle cartelle
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")

# Crea le cartelle se non esistono
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def encode_document(file, chunk_size, overlap, fps, frame_size):
    """
    Codifica un documento (PDF o testo) in formato Memvid.
    
    Args:
        file: File caricato tramite Gradio
        chunk_size: Dimensione dei chunk di testo
        overlap: Sovrapposizione tra i chunk
        fps: Frame per secondo per il video
        frame_size: Dimensione del frame per i codici QR
    
    Returns:
        str: Percorso al file video MP4 generato
        str: Percorso al file indice JSON
        str: Messaggio di conferma o errore
    """
    try:
        # Verifica se il file esiste
        if file is None:
            return None, None, "Nessun file caricato. Seleziona un file PDF o di testo."

        print(f"File ricevuto: {type(file)}, {file}")
        
        # Gestione specifica per i diversi tipi di oggetti che Gradio può fornire
        if hasattr(file, "name"):
            # È probabilmente un oggetto File di Gradio
            file_name = file.name
            file_path = os.path.join(UPLOAD_FOLDER, file_name)
            
            # In Gradio 4+, il file potrebbe essere già sul disco
            if hasattr(file, "path") and os.path.exists(file.path):
                file_path = file.path
            else:
                # Se è un buffer o un oggetto che supporta read()
                if hasattr(file, "read") and callable(file.read):
                    # Scrivi il contenuto sul disco
                    with open(file_path, "wb") as f:
                        content = file.read()
                        if isinstance(content, str):
                            content = content.encode('utf-8')
                        f.write(content)
                # Riavvolgi il file se supporta la funzione seek
                if hasattr(file, "seek") and callable(file.seek):
                    try:
                        file.seek(0)
                    except:
                        pass
        elif isinstance(file, str):
            # È un percorso di file
            file_path = file
            file_name = os.path.basename(file)
        else:
            return None, None, f"Tipo di file non supportato: {type(file)}. Riprova con un altro file."
        
        # Verifica che il file esista sul disco
        if not os.path.exists(file_path):
            return None, None, f"File non trovato sul disco: {file_path}"

        print(f"File path: {file_path}")
        
        # Determina il tipo di file
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # Crea nomi di output
        base_name = os.path.splitext(os.path.basename(file_name))[0]
        output_video = os.path.join(OUTPUT_FOLDER, f"{base_name}.mp4")
        output_index = os.path.join(OUTPUT_FOLDER, f"{base_name}_index.json")
        
        # Inizializza l'encoder (senza parametri poiché non li accetta)
        encoder = MemvidEncoder()
        
        # Aggiungi il documento appropriato in base al tipo di file
        if file_extension == ".pdf":
            # Per i PDF, possiamo passare chunk_size e overlap direttamente al metodo
            encoder.add_pdf(file_path, chunk_size=chunk_size, overlap=overlap)
        elif file_extension in [".txt", ".md", ".markdown"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Passa chunk_size e overlap direttamente al metodo add_text
            encoder.add_text(content, chunk_size=chunk_size, overlap=overlap)
        else:
            return None, None, f"Formato file non supportato: {file_extension}. Usa PDF, TXT o MD."
        
        # Costruisci il video
        encoder.build_video(
            output_video, 
            output_index,
            fps=fps,
            frame_size=frame_size
        )
        
        return output_video, output_index, f"Documento codificato con successo in formato Memvid!"
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        print(f"Errore completo:\n{traceback_str}")
        return None, None, f"Errore durante la codifica: {str(e)}\nTipo del file: {type(file)}\nDettagli: {traceback_str}"

# Interfaccia Gradio
with gr.Blocks(title="Memvid Document Encoder") as app:
    gr.Markdown("# 📚 Memvid Document Encoder")
    gr.Markdown(
        """Carica un documento PDF o un file di testo/markdown per codificarlo in formato Memvid.
        Memvid converte i tuoi documenti in un file video MP4 con codici QR, creando una knowledge base altamente compressa."""
    )
    
    with gr.Row():
        with gr.Column(scale=2):
            # Input di caricamento file
            file_input = gr.File(
                label="Carica PDF o file di testo",
                file_types=[".pdf", ".txt", ".md", ".markdown"],
                type="filepath"  # Questo è importante - dice a Gradio di passare il percorso del file
            )
            
            # Parametri di codifica
            with gr.Accordion("Parametri avanzati", open=False):
                chunk_size = gr.Slider(128, 2048, 512, step=32, label="Dimensione Chunk (caratteri)")
                overlap = gr.Slider(0, 200, 50, step=10, label="Sovrapposizione (caratteri)")
                fps = gr.Slider(1, 60, 30, step=1, label="FPS (frame per secondo)")
                frame_size = gr.Slider(128, 1024, 256, step=32, label="Dimensione Frame")
            
            # Pulsante di elaborazione
            encode_btn = gr.Button("Codifica Documento", variant="primary")
        
        with gr.Column(scale=3):
            # Output
            output_video = gr.File(label="Video MP4 generato")
            output_index = gr.File(label="File indice JSON")
            output_message = gr.Textbox(label="Stato", max_lines=10)  # Aumenta il numero di righe per mostrare più dettagli
    
    # Connetti la funzione al pulsante
    encode_btn.click(
        fn=encode_document,
        inputs=[file_input, chunk_size, overlap, fps, frame_size],
        outputs=[output_video, output_index, output_message]
    )
    
    gr.Markdown(
        """## Come funziona
        
        1. **Chunking**: Il documento viene suddiviso in piccoli frammenti di testo
        2. **Embedding**: Ogni frammento viene convertito in un vettore numerico per la ricerca semantica
        3. **QR Code**: I frammenti vengono codificati come codici QR
        4. **Video MP4**: I codici QR vengono assemblati in un video compresso
        
        Il risultato è una knowledge base altamente compressa e facilmente interrogabile.
        """
    )

if __name__ == "__main__":
    # Specifichiamo esplicitamente l'indirizzo IP e la porta
    app.launch(server_name="0.0.0.0", server_port=7860, share=True)
