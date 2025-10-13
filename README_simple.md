# Memvid Document Encoder (Versione Semplice)

Un'applicazione web semplice per codificare documenti PDF e file di testo in formato Memvid.

## Cos'è Memvid?

Memvid è una libreria Python che permette di codificare testi in video di codici QR, creando knowledge base altamente compresse e portabili che possono essere interrogate semanticamente.

## Come usare questa app

1. Avvia l'app con `python simple_app.py` o facendo doppio clic su `start_simple.bat`
2. Carica un file PDF o un file di testo/markdown nell'interfaccia
3. Premi il pulsante "Processa File"
4. Attendi il completamento dell'elaborazione
5. I file generati (MP4 e JSON) saranno salvati nella cartella `outputs`

## Cartelle

- `uploads/`: Cartella temporanea per i file caricati
- `outputs/`: Cartella per i file video e indici generati

## API di Memvid utilizzata

```python
# Inizializzazione
encoder = MemvidEncoder()

# Aggiunta di documenti PDF
encoder.add_pdf(file_path, chunk_size=500, overlap=50)

# Aggiunta di testo
encoder.add_text(content, chunk_size=500, overlap=50)

# Generazione del video
encoder.build_video(output_video, output_index)
```
