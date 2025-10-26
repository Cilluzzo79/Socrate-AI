"""
Script da riga di comando per elaborare file in formato Memvid con approccio a sezioni.
Versione compatibile con Windows con protezione anti-loop e monitoraggio avanzato.
"""
import os
import sys
import json
import re
import argparse
import time
from pathlib import Path
import gc  # Garbage Collector
import math
import threading
import traceback

# Variabili per il monitoraggio dell'attività
activity_timestamp = time.time()
current_activity = "Inizializzazione"
last_positions = []  # Per rilevare loop di posizione

# Verifica se memvid è installato (solo per output video)
# Per JSON-only mode, memvid non è necessario
try:
    from memvid import MemvidEncoder
    MEMVID_AVAILABLE = True
except ImportError:
    MEMVID_AVAILABLE = False
    print("⚠️ memvid non disponibile - solo output JSON sarà supportato")

# Funzione per aggiornare l'attività corrente
def update_activity(activity):
    global activity_timestamp, current_activity
    current_activity = activity
    activity_timestamp = time.time()
    print(f"[ATTIVITÀ] {activity}")

# Thread per monitorare l'attività
def activity_monitor():
    global activity_timestamp, current_activity
    while True:
        time.sleep(10)  # Controlla ogni 10 secondi
        elapsed = time.time() - activity_timestamp
        if elapsed > 20:  # Se nessun aggiornamento da 20 secondi, mostra un messaggio
            print(f"[MONITOR] Ancora in esecuzione: '{current_activity}' - {int(elapsed)}s senza aggiornamenti")
        
        # Garbage collection forzato periodicamente
        gc.collect()

# Funzione per verificare se siamo bloccati in un loop
def check_loop(start_position, text_length, chunk_index):
    global last_positions
    
    # Aggiungi la posizione corrente all'elenco
    last_positions.append((start_position, chunk_index))
    
    # Mantieni solo le ultime 20 posizioni
    if len(last_positions) > 20:
        last_positions.pop(0)
    
    # Se abbiamo almeno 10 posizioni, verifica se siamo bloccati
    if len(last_positions) >= 10:
        # Conta le posizioni uniche
        unique_positions = len(set([pos for pos, _ in last_positions]))
        
        # Se tutte le ultime 10 posizioni sono identiche, siamo bloccati
        if unique_positions == 1:
            print(f"[ERRORE] Rilevato loop di posizione: bloccato a {start_position}/{text_length}")
            return True
        
        # Se l'indice del chunk continua ad aumentare ma la posizione rimane la stessa
        if unique_positions <= 2 and last_positions[-1][1] - last_positions[0][1] >= 10:
            print(f"[ERRORE] Rilevato loop di generazione: stesso punto ma chunk diversi")
            return True
    
    return False

# Implementazione timeout compatibile con Windows
class TimeoutError(Exception):
    pass

def timeout_handler(function, args=(), kwargs={}, timeout_duration=10):
    """Implementazione timeout usando threading (compatibile con tutti i sistemi)"""
    result = [None]
    error = [None]
    finished = [False]
    
    def target():
        try:
            result[0] = function(*args, **kwargs)
            finished[0] = True
        except Exception as e:
            error[0] = e
            finished[0] = True
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    update_activity(f"Avvio funzione con timeout {timeout_duration}s")
    thread.start()
    thread.join(timeout_duration)
    
    if finished[0]:
        if error[0] is not None:
            raise error[0]
        return result[0]
    else:
        raise TimeoutError(f"Operazione interrotta per timeout dopo {timeout_duration} secondi")

def read_file_in_sections(file_path, section_size=50000, max_pages=None):
    """
    Legge un file dividendolo in sezioni gestibili.
    Restituisce una lista di sezioni di testo.
    
    Args:
        file_path: Percorso del file
        section_size: Dimensione massima di ogni sezione in caratteri
        max_pages: Numero massimo di pagine da elaborare (solo per PDF)
    
    Returns:
        List[str]: Lista di sezioni di testo
    """
    update_activity(f"Lettura del file {file_path} in sezioni...")
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # PDF - elaborazione speciale
    if file_extension == ".pdf":
        try:
            import PyPDF2
            sections = []
            current_section = ""
            current_size = 0
            
            update_activity(f"Apertura file PDF {file_path}")
            with open(file_path, "rb") as f:
                update_activity("Creazione PDF reader")
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
                pages_to_extract = total_pages if max_pages is None else min(max_pages, total_pages)
                print(f"File PDF con {total_pages} pagine. Estrazione di {pages_to_extract} pagine...")
                
                for i in range(pages_to_extract):
                    if i % 5 == 0:  # Aggiornamento ogni 5 pagine
                        print(f"Estrazione pagina {i+1}/{pages_to_extract}...")
                    
                    update_activity(f"Estrazione pagina {i+1}/{pages_to_extract}")
                    try:
                        # Estrai la pagina con timeout
                        def extract_page():
                            update_activity(f"Lettura pagina {i+1} dal reader")
                            page = reader.pages[i]
                            update_activity(f"Estrazione testo dalla pagina {i+1}")
                            return page.extract_text() or ""
                        
                        try:
                            page_text = timeout_handler(extract_page, timeout_duration=20)
                        except TimeoutError:
                            print(f"Timeout nell'estrazione della pagina {i+1}, saltando...")
                            page_text = f"[Timeout durante l'estrazione della pagina {i+1}]"
                        
                        update_activity(f"Elaborazione testo pagina {i+1} (lunghezza: {len(page_text)} caratteri)")
                        if page_text.strip():
                            page_content = f"\n## Pagina {i+1}\n\n{page_text}\n\n"
                            
                            # Se aggiungendo questa pagina superiamo la dimensione massima, 
                            # avviamo una nuova sezione
                            if current_size + len(page_content) > section_size and current_size > 0:
                                sections.append(current_section)
                                current_section = page_content
                                current_size = len(page_content)
                                print(f"Nuova sezione iniziata alla pagina {i+1}")
                            else:
                                current_section += page_content
                                current_size += len(page_content)
                        
                        # Pulizia della memoria dopo ogni pagina
                        update_activity(f"Pulizia memoria dopo pagina {i+1}")
                        page_text = None
                        gc.collect()
                    except Exception as e:
                        print(f"Errore nell'estrazione della pagina {i+1}: {str(e)}")
                        current_section += f"\n## Pagina {i+1} (errore)\n\n"
                    
                    # Forza una nuova sezione ogni 15 pagine per sicurezza (ridotto da 20)
                    if (i + 1) % 15 == 0 and current_section:
                        update_activity(f"Forzatura nuova sezione dopo pagina {i+1}")
                        sections.append(current_section)
                        current_section = ""
                        current_size = 0
                        print(f"Nuova sezione forzata dopo la pagina {i+1}")
                        # Forza garbage collection
                        gc.collect()
                
                # Aggiungiamo l'ultima sezione
                if current_section:
                    update_activity("Aggiunta ultima sezione")
                    sections.append(current_section)
                
                print(f"File diviso in {len(sections)} sezioni")
                return sections
        except Exception as e:
            print(f"Errore nella lettura del PDF: {str(e)}")
            print(traceback.format_exc())
            return []
    
    # Altri formati di testo - lettura per blocchi
    else:
        try:
            update_activity("Determinazione codifica del file")
            # Determinare la codifica
            encoding = "utf-8"
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    f.read(100)  # Prova a leggere alcuni caratteri
            except UnicodeDecodeError:
                encoding = "latin-1"
                print(f"Usando codifica {encoding}")
            
            # Ottiene le dimensioni del file
            file_size = os.path.getsize(file_path)
            # Usa sezioni più piccole per file grandi
            if file_size > 1000000:  # 1MB
                section_size = min(section_size, 50000)  # 50KB per file grandi
                
            num_sections = math.ceil(file_size / section_size)
            
            update_activity(f"Lettura file di testo in {num_sections} sezioni")
            # Legge il file in sezioni
            sections = []
            with open(file_path, "r", encoding=encoding) as f:
                for i in range(num_sections):
                    update_activity(f"Lettura sezione {i+1}/{num_sections}")
                    print(f"Lettura sezione {i+1}/{num_sections}...")
                    section_text = f.read(section_size)
                    
                    # Se siamo a metà di una riga, leggiamo fino alla fine della riga
                    if i < num_sections - 1 and not section_text.endswith("\n"):
                        update_activity(f"Completamento riga in sezione {i+1}")
                        # Legge caratteri finché non trova una nuova riga o EOF
                        char = f.read(1)
                        while char and char != "\n":
                            section_text += char
                            char = f.read(1)
                        if char == "\n":
                            section_text += char
                    
                    if section_text:
                        sections.append(section_text)
                
                print(f"File diviso in {len(sections)} sezioni")
                return sections
        except Exception as e:
            print(f"Errore nella lettura del file: {str(e)}")
            print(traceback.format_exc())
            return []

def divide_text_into_chunks(text, chunk_size, overlap, max_chunks_per_section=2000):
    """
    Divide il testo in chunk con sovrapposizione, rispettando frasi e paragrafi.
    Versione con protezione anti-loop e limite massimo di chunk per sezione.
    
    Args:
        text: Testo da dividere
        chunk_size: Dimensione massima di ciascun chunk
        overlap: Sovrapposizione tra chunk consecutivi
        max_chunks_per_section: Limite massimo di chunk per sezione
    
    Returns:
        List[Dict]: Lista di chunk con metadati
    """
    if not text:
        return []
    
    update_activity(f"Divisione testo di {len(text)} caratteri in chunks")
    chunks = []
    start = 0
    chunk_index = 0
    text_length = len(text)
    last_start = -1  # Per rilevare se non stiamo avanzando
    loop_count = 0  # Per contare quante volte non avanziamo
    
    # Verifico se il testo è più piccolo della dimensione del chunk
    if text_length <= chunk_size:
        update_activity(f"Creazione chunk unico (testo più piccolo di chunk_size)")
        metadata = {
            "index": 0,
            "start": 0,
            "end": text_length,
            "length": text_length
        }
        
        # Cerca di estrarre un possibile titolo
        lines = text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) < 100:
                metadata["title"] = line
                break
                
        chunks.append({
            "text": text,
            "metadata": metadata
        })
        return chunks
    
    update_activity(f"Iniziata divisione in chunk (text_length: {text_length})")
    progress_interval = max(1, text_length // (chunk_size * 10))  # Report ogni ~10 chunks
    
    while start < text_length and chunk_index < max_chunks_per_section:
        # Aggiornamenti periodici di attività
        if chunk_index % progress_interval == 0:
            update_activity(f"Elaborazione chunk {chunk_index+1} - posizione {start}/{text_length} ({(start/text_length*100):.1f}%)")
        
        # Verifica se siamo bloccati in un loop
        if check_loop(start, text_length, chunk_index):
            print(f"[AVVISO] Possibile loop rilevato, forzando avanzamento...")
            # Forza l'avanzamento di almeno il 10% della dimensione del chunk
            start += max(int(chunk_size * 0.1), 1)
            # Se ancora nella stessa posizione, interrompi il ciclo
            if start == last_start:
                print(f"[ERRORE] Impossibile avanzare oltre la posizione {start}, interrompo l'elaborazione")
                break
            loop_count = 0
            continue
        
        # Rileva se non stiamo avanzando
        if start == last_start:
            loop_count += 1
            if loop_count >= 5:  # Dopo 5 tentativi
                print(f"[AVVISO] Non riesco ad avanzare dalla posizione {start}, forzando avanzamento...")
                # Forza l'avanzamento di almeno il 5% della dimensione del chunk
                start += max(int(chunk_size * 0.05), 1)
                loop_count = 0
                continue
        else:
            loop_count = 0
        
        last_start = start
        
        # Calcola la fine del chunk
        end = min(start + chunk_size, text_length)
        
        # Se non siamo alla fine, cerca un punto di interruzione naturale
        if end < text_length:
            # Prima prova a trovare la fine di un paragrafo
            paragraph_end = text.rfind("\n\n", start, end)
            
            # Se non c'è un paragrafo, cerca la fine di una frase
            sentence_end = text.rfind(". ", start, end)
            
            # Usa il punto di interruzione più lontano trovato
            if paragraph_end > start + 200:  # Almeno 200 caratteri di contenuto
                end = paragraph_end + 2
            elif sentence_end > start + 200:
                end = sentence_end + 2
        
        # Controllo di sicurezza: assicurati che end > start
        if end <= start:
            print(f"[ERRORE] Fine del chunk ({end}) non maggiore dell'inizio ({start}), forzando avanzamento")
            start += max(int(chunk_size * 0.1), 1)
            continue
        
        # Estrai il chunk con FORWARD OVERLAP per catturare contenuto della pagina successiva
        chunk_text = text[start:end]

        # FORWARD OVERLAP FIX: Aggiungi i primi 400 caratteri DOPO questo chunk
        # Questo risolve il problema di liste/contenuti che vanno a capo su nuova pagina
        forward_overlap_size = 400
        if end < text_length:
            forward_end = min(end + forward_overlap_size, text_length)
            forward_text = text[end:forward_end]
            if forward_text:
                chunk_text = chunk_text + forward_text
                print(f"[FORWARD OVERLAP] Chunk {chunk_index}: aggiunto forward overlap di {len(forward_text)} chars")

        # Crea metadati di base
        metadata = {
            "index": chunk_index,
            "start": start,
            "end": end,  # Mantiene end originale per calcolo avanzamento
            "length": len(chunk_text),  # La lunghezza include il forward overlap
            "has_forward_overlap": end < text_length  # Flag per indicare presenza di forward overlap
        }
        
        # Cerca di estrarre un possibile titolo
        lines = chunk_text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and line.startswith('##'):  # Titoli in formato Markdown
                metadata["title"] = line
                break
            elif line and len(line) < 100 and not line.endswith('.'):  # Titoli probabili
                metadata["title"] = line
                break
        
        # Cerca riferimenti alla pagina
        page_match = re.search(r'## Pagina (\d+)', chunk_text)
        if page_match:
            metadata["page"] = int(page_match.group(1))
        
        chunks.append({
            "text": chunk_text,
            "metadata": metadata
        })
        
        # Avanzamento con sovrapposizione
        new_start = end - overlap
        
        # Controllo di sicurezza: assicurati che stiamo avanzando
        if new_start <= start:
            print(f"[AVVISO] Nuova posizione ({new_start}) non maggiore della precedente ({start}), forzando avanzamento")
            new_start = start + max(int(chunk_size * 0.05), 1)
        
        start = new_start
        chunk_index += 1
        
        # Garbage collection periodico
        if chunk_index % 100 == 0:
            gc.collect()
    
    # Se abbiamo raggiunto il limite massimo di chunk
    if chunk_index >= max_chunks_per_section and start < text_length:
        print(f"[AVVISO] Raggiunto limite massimo di {max_chunks_per_section} chunk per sezione.")
        print(f"Elaborazione interrotta al {(start/text_length*100):.1f}% del testo")
    
    update_activity(f"Completata divisione in {len(chunks)} chunks")
    return chunks

def process_file_in_sections(file_path, chunk_size, overlap, output_format="mp4", max_pages=None, max_chunks=None):
    """
    Elabora un file in sezioni per garantire l'elaborazione completa.
    
    Args:
        file_path: Percorso del file da elaborare
        chunk_size: Dimensione massima di ciascun chunk
        overlap: Sovrapposizione tra chunk consecutivi
        output_format: Formato dell'output ("mp4" o "json")
        max_pages: Numero massimo di pagine da elaborare (solo per PDF)
        max_chunks: Numero massimo di chunk totali da creare
    
    Returns:
        bool: True se l'elaborazione è stata completata con successo
    """
    if not os.path.exists(file_path):
        print(f"Errore: File non trovato: {file_path}")
        return False
    
    try:
        start_time = time.time()
        update_activity(f"Inizio elaborazione di {file_path} in sezioni...")
        print(f"Parametri: chunk_size={chunk_size}, overlap={overlap}, format={output_format}")
        
        # Resetta le variabili di monitoraggio
        global last_positions
        last_positions = []
        
        # Avvia il thread di monitoraggio
        monitor_thread = threading.Thread(target=activity_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Crea le cartelle di output se non esistono
        update_activity("Creazione directory di output")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "outputs")
        os.makedirs(output_dir, exist_ok=True)
        
        # Leggi il file in sezioni
        sections = read_file_in_sections(file_path, section_size=50000, max_pages=max_pages)
        if not sections:
            update_activity("Errore: Nessuna sezione letta dal file.")
            return False
        
        # Elabora ogni sezione
        all_chunks = []
        previous_section_tail = ""  # Store last part of previous section for overlap

        for i, section in enumerate(sections):
            update_activity(f"Elaborazione sezione {i+1}/{len(sections)}...")
            print(f"\nElaborazione sezione {i+1}/{len(sections)}...")

            # INTER-SECTION OVERLAP FIX: Add overlap from previous section
            if i > 0 and previous_section_tail:
                # Prepend last 'overlap' characters from previous section
                section_with_overlap = previous_section_tail + section
                print(f"[OVERLAP FIX] Aggiunto overlap di {len(previous_section_tail)} caratteri dalla sezione precedente")
            else:
                section_with_overlap = section

            print(f"Dimensione della sezione: {len(section_with_overlap)} caratteri")

            # Dividi la sezione in chunk con limite di sicurezza
            section_chunks = divide_text_into_chunks(section_with_overlap, chunk_size, overlap, max_chunks_per_section=2000)
            print(f"Generati {len(section_chunks)} chunk dalla sezione {i+1}")

            # Se la sezione ha prodotto zero chunk, salta
            if not section_chunks:
                print(f"[AVVISO] La sezione {i+1} non ha prodotto chunk, potrebbe esserci un problema")
                previous_section_tail = ""
                continue

            # Store tail of current section for next iteration
            # Use 2x overlap to ensure we capture boundary content
            tail_size = min(overlap * 2, len(section))
            previous_section_tail = section[-tail_size:] if tail_size > 0 else ""

            # Aggiungi gli offset corretti agli indici
            update_activity(f"Aggiornamento indici per {len(section_chunks)} chunks")
            offset = len(all_chunks)
            for j, chunk in enumerate(section_chunks):
                chunk["metadata"]["index"] = offset + j
                chunk["metadata"]["section"] = i + 1
                chunk["metadata"]["total_sections"] = len(sections)

            # Aggiungi i chunk alla lista completa
            all_chunks.extend(section_chunks)
            
            # Controllo del numero massimo di chunk
            if max_chunks and len(all_chunks) >= max_chunks:
                update_activity(f"Raggiunto il limite massimo di {max_chunks} chunk.")
                all_chunks = all_chunks[:max_chunks]
                break
            
            # Pulizia della memoria dopo ogni sezione
            update_activity(f"Pulizia memoria dopo sezione {i+1}")
            section = None
            section_chunks = None
            gc.collect()
        
        update_activity(f"Generati {len(all_chunks)} chunk totali da {len(sections)} sezioni")
        print(f"\nGenerati {len(all_chunks)} chunk totali da {len(sections)} sezioni")
        
        # Se non sono stati generati chunk, termina
        if not all_chunks:
            update_activity("Errore: Nessun chunk generato, impossibile procedere.")
            return False
        
        # Estrai solo il testo per l'elaborazione Memvid
        update_activity("Estrazione testo per Memvid")
        chunks_text = [c["text"] for c in all_chunks]
        
        # Crea i nomi dei file di output
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        metadata_file = os.path.join(output_dir, f"{base_name}_sections_metadata.json")
        
        # Salva i metadati
        update_activity(f"Salvataggio dei metadati in {metadata_file}...")
        print(f"Salvataggio dei metadati in {metadata_file}...")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump({
                "file": os.path.basename(file_path),
                "chunk_size": chunk_size,
                "overlap": overlap,
                "chunks_count": len(all_chunks),
                "sections_count": len(sections),
                "total_text_length": sum(len(c["text"]) for c in all_chunks),
                "processing_info": {
                    "max_chunks_setting": max_chunks,
                    "processing_time": time.time() - start_time
                },
                "chunks": all_chunks
            }, f, indent=2)
        
        # Libera memoria
        update_activity("Pulizia memoria prima della generazione video")
        all_chunks = None
        gc.collect()
        
        # Se richiesto solo JSON, termina qui
        if output_format == "json":
            elapsed_time = time.time() - start_time
            update_activity(f"Elaborazione completata in {elapsed_time:.2f} secondi")
            print(f"Elaborazione completata in {elapsed_time:.2f} secondi")
            print(f"File di metadati: {metadata_file}")
            return True
        
        # Altrimenti, crea il video Memvid
        if not MEMVID_AVAILABLE:
            print("❌ memvid non disponibile - impossibile generare video MP4")
            print("✅ File JSON generato con successo")
            return True

        output_video = os.path.join(output_dir, f"{base_name}_sections.mp4")
        output_index = os.path.join(output_dir, f"{base_name}_sections_index.json")

        # Crea l'encoder
        update_activity("Creazione dell'encoder Memvid...")
        print("Creazione dell'encoder Memvid...")
        encoder = MemvidEncoder()
        
        # Aggiungi i chunk in batch per risparmiare memoria
        batch_size = 20  # Elabora 20 chunk alla volta
        for i in range(0, len(chunks_text), batch_size):
            batch_end = min(i + batch_size, len(chunks_text))
            update_activity(f"Aggiunta batch {i//batch_size + 1}/{(len(chunks_text) + batch_size - 1)//batch_size}...")
            print(f"Aggiunta batch {i//batch_size + 1}/{(len(chunks_text) + batch_size - 1)//batch_size}...")
            
            batch_chunks = chunks_text[i:batch_end]
            encoder.add_chunks(batch_chunks)
            
            # Pulizia batch
            batch_chunks = None
            gc.collect()
        
        # Libera memoria dei chunk
        update_activity("Pulizia memoria prima della generazione del video")
        chunks_text = None
        gc.collect()
        
        # Costruisci il video
        update_activity(f"Generazione del video in {output_video}...")
        print(f"Generazione del video in {output_video}...")
        encoder.build_video(output_video, output_index)
        
        # Libera l'encoder
        update_activity("Pulizia finale e completamento")
        encoder = None
        gc.collect()
        
        elapsed_time = time.time() - start_time
        print(f"Elaborazione completata in {elapsed_time:.2f} secondi")
        print(f"File generati:")
        print(f"- Video: {output_video}")
        print(f"- Indice: {output_index}")
        print(f"- Metadati: {metadata_file}")
        
        return True
    
    except Exception as e:
        update_activity(f"ERRORE CRITICO: {str(e)}")
        import traceback
        print(f"Errore durante l'elaborazione: {str(e)}")
        print(traceback.format_exc())
        return False

def main():
    """Funzione principale"""
    parser = argparse.ArgumentParser(description='Memvid Sections Encoder - Elabora file in sezioni per garantire l\'elaborazione completa')
    parser.add_argument('file', help='Percorso del file da elaborare')
    parser.add_argument('--chunk-size', type=int, default=1200, help='Dimensione dei chunk (default: 1200)')
    parser.add_argument('--overlap', type=int, default=200, help='Sovrapposizione tra chunk (default: 200)')
    parser.add_argument('--format', choices=['mp4', 'json'], default='mp4', help='Formato output (default: mp4)')
    parser.add_argument('--max-pages', type=int, help='Numero massimo di pagine da elaborare (solo per PDF)')
    parser.add_argument('--max-chunks', type=int, help='Numero massimo di chunk da creare (default: nessun limite)')
    
    args = parser.parse_args()
    
    update_activity("Avvio elaborazione con parameters: " + str(args))
    success = process_file_in_sections(
        args.file, 
        args.chunk_size, 
        args.overlap, 
        args.format,
        args.max_pages,
        args.max_chunks
    )
    
    update_activity("Processo completato con stato: " + ("successo" if success else "fallimento"))
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
