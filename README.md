# Memvid Document Encoder

Un'interfaccia web semplice per codificare documenti PDF e file di testo in formato Memvid.

## Cos'è Memvid?

Memvid è una libreria Python per la creazione di knowledge base basate su video QR code che permette:

- Suddividere e codificare dati testuali in video di codici QR
- Ricerca semantica veloce e recupero dai video QR
- Interfaccia conversazionale AI con memoria contestuale

## Come usare questa app

1. Avvia l'app con `python run.py`
2. Carica un file PDF o un file di testo/markdown
3. Regola i parametri avanzati (opzionale)
4. Premi il pulsante "Codifica Documento"
5. Scarica il file video MP4 e il file indice JSON generati

## Parametri avanzati

- **Dimensione Chunk**: Quanti caratteri includere in ogni frammento di testo (chunk)
- **Sovrapposizione**: Quanti caratteri sovrapporre tra chunk consecutivi
- **FPS**: Frame per secondo nel video generato (influenza la densità di dati)
- **Dimensione Frame**: Dimensione dei frame del codice QR (in pixel)

## Struttura dei file

- `uploads/`: Cartella per i file caricati
- `outputs/`: Cartella per i file generati
- `debug.py`: Script per verificare l'ambiente
- `check_api.py`: Script per verificare l'API di Memvid
- `esempio_base.py`: Esempio di utilizzo senza interfaccia
- `simple_app.py`: Versione semplificata dell'interfaccia web

## API di Memvid

Da notare che l'API di Memvid ha alcune particolarità:

```python
# Inizializzazione
encoder = MemvidEncoder()  # Non accetta chunk_size/overlap nel costruttore

# Aggiunta di documenti PDF
encoder.add_pdf(file_path, chunk_size=500, overlap=50)  # Parametri di chunking qui

# Aggiunta di testo
encoder.add_text(content, chunk_size=500, overlap=50)  # Parametri di chunking qui

# Aggiunta di chunks pre-elaborati
encoder.add_chunks(["chunk1", "chunk2", "chunk3"])  # Non accetta source

# Generazione del video
encoder.build_video(output_video, output_index) 
```

## Tecnologia

Questo progetto utilizza la tecnologia Memvid per convertire i dati testuali in codici QR, che vengono poi assemblati in un file video MP4. Questo approccio offre:

- Compressione estrema (50-100 volte più piccolo dei database vettoriali tradizionali)
- Portabilità (nessuna infrastruttura di database necessaria)
- Ricerca semantica veloce anche offline

