"""
Versione semplificata dell'encoder Memvid con interfaccia minimale.
Utilizzare questa versione in caso di problemi con l'interfaccia principale.
"""
import os
import sys
import gradio as gr

# Assicurati che memvid sia importato
try:
    from memvid import MemvidEncoder
except ImportError:
    print("ERRORE: memvid non è installato. Installalo con 'pip install memvid'")
    sys.exit(1)

# Configurazione delle cartelle
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")

# Crea le cartelle se non esistono
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_file(file_path):
    """
    Processa un file e crea un video Memvid.
    
    Args:
        file_path: Percorso del file da processare
    
    Returns:
        str: Messaggio di stato
    """
    if not file_path:
        return "Nessun file selezionato."
    
    try:
        # Verifica che il file esista
        if not os.path.exists(file_path):
            return f"File non trovato: {file_path}"
            
        # Ottieni l'estensione del file
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in [".pdf", ".txt", ".md", ".markdown"]:
            return f"Formato file non supportato: {file_extension}. Usa PDF, TXT o MD."
            
        # Crea i nomi dei file di output
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_video = os.path.join(OUTPUT_FOLDER, f"{base_name}.mp4")
        output_index = os.path.join(OUTPUT_FOLDER, f"{base_name}_index.json")
        
        # Crea l'encoder
        encoder = MemvidEncoder()
        
        # Parametri di chunking
        chunk_size = 500  # Dimensione predefinita del chunk
        overlap = 50      # Sovrapposizione predefinita
        
        # Aggiungi il contenuto del file
        if file_extension == ".pdf":
            encoder.add_pdf(file_path, chunk_size=chunk_size, overlap=overlap)
        else:  # File di testo
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Usa direttamente i parametri supportati
            encoder.add_text(content, chunk_size=chunk_size, overlap=overlap)
        
        # Costruisci il video
        encoder.build_video(output_video, output_index)
        
        return f"""
        File processato con successo!
        
        Video creato: {output_video}
        Indice creato: {output_index}
        
        Dimensione video: {os.path.getsize(output_video) / 1024:.2f} KB
        """
    except Exception as e:
        import traceback
        return f"Errore durante l'elaborazione: {str(e)}\n\n{traceback.format_exc()}"

# Crea l'interfaccia
with gr.Blocks(title="Memvid Simple Encoder") as app:
    gr.Markdown("# 📚 Memvid Simple Encoder")
    gr.Markdown("Versione semplificata per codificare documenti in formato Memvid.")
    
    file_input = gr.File(label="Seleziona un file", file_types=[".pdf", ".txt", ".md", ".markdown"], type="filepath")
    process_btn = gr.Button("Processa File", variant="primary")
    result = gr.Textbox(label="Risultato", lines=10)
    
    process_btn.click(fn=process_file, inputs=file_input, outputs=result)

if __name__ == "__main__":
    print("Avvio dell'interfaccia semplificata Memvid...")
    print("Al termine dell'avvio, apri il browser all'indirizzo: http://localhost:7861")
    app.launch(server_name="0.0.0.0", server_port=7861, share=True)
