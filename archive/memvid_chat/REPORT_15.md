# Report 15: Risoluzione Problema Telegram Callback Data

## Data
27 settembre 2025

## Problema Identificato

Dopo l'esecuzione dello script di debug per la selezione dei documenti nel bot Telegram, è stato identificato un problema specifico:

```
__main__ - INFO - Aggiungo bottone: mind_magic_the_neuroscience_of_manifestation_and_how_it_changes 2 (17.9 MB) -> doc:mind_magic_the_neuroscience_of_manifestation_and_how_it_changes 2
__main__ - WARNING - ATTENZIONE: callback_data troppo lungo! (69 caratteri)
```

Il problema è dovuto a una limitazione dell'API Telegram: il campo `callback_data` dei bottoni inline ha un limite massimo di 64 byte. Nel nostro caso, alcuni nomi di documenti sono troppo lunghi e, combinati con il prefisso "doc:", superano questo limite, causando errori quando l'utente tenta di selezionare questi documenti.

## Soluzione Implementata

Abbiamo implementato una strategia per gestire i nomi di documenti lunghi:

### 1. Troncamento Intelligente nel Selettore di Documenti

Il metodo `select_document` è stato modificato per controllare la lunghezza del `callback_data` prima di creare il bottone:

```python
# Truncate document_id if too long (Telegram has 64-byte limit for callback_data)
callback_id = doc.document_id
if len(doc_pattern + callback_id) > 60:  # Leave some margin
    # Use a numeric id instead for long names
    callback_id = f"id:{doc.id}"
    logger.info(f"Using shortened callback for long document name: {doc.document_id} -> {callback_id}")
```

Quando il nome del documento è troppo lungo, utilizziamo invece l'ID numerico interno del documento nel database, con il prefisso "id:" per distinguerlo dai nomi diretti.

### 2. Gestione del Callback con ID Numerico

Il metodo `document_selected` è stato aggiornato per gestire sia i riferimenti diretti che quelli numerici:

```python
# Check if we're using a numeric ID
if data.startswith("id:"):
    # Extract numeric ID
    try:
        doc_id = int(data.split(":")[1])
        # Get document from database by numeric ID
        from database.models import Document, get_session
        session = get_session()
        document = session.query(Document).filter(Document.id == doc_id).first()
        session.close()
        
        if not document:
            logger.error(f"Document with numeric ID {doc_id} not found")
            await query.edit_message_text(text="Document not found. Please try again.")
            return ConversationHandler.END
            
        # Use the document_id from the database
        document_id = document.document_id
        logger.info(f"Retrieved document by numeric ID: {doc_id} -> {document_id}")
    except Exception as e:
        logger.error(f"Error retrieving document by numeric ID: {e}", exc_info=True)
        await query.edit_message_text(text="Error retrieving document. Please try again.")
        return ConversationHandler.END
else:
    # Use the document_id directly
    document_id = data
```

### 3. Miglioramento nella Formattazione delle Dimensioni

Abbiamo anche migliorato la formattazione delle dimensioni dei file nei bottoni:

```python
# Format size with 1 decimal place
size_text = f"{doc.size_mb:.1f} MB" if doc.size_mb >= 1 else f"{doc.size_mb*1024:.0f} KB"
```

### 4. Gestione degli Errori Robusta

Entrambi i metodi sono stati migliorati con un'adeguata gestione degli errori:

- Try/except intorno alle operazioni principali
- Logging dettagliato di errori ed eccezioni
- Messaggi utente informativi in caso di problemi

## Vantaggi della Soluzione

1. **Compatibilità con l'API Telegram**: Rispetta il limite di 64 byte per il `callback_data`
2. **Trasparenza per l'Utente**: L'utente vede ancora il nome completo del documento nel bottone
3. **Resilienza**: Gestione adeguata degli errori con messaggi informativi
4. **Tracciabilità**: Logging dettagliato per facilitare il debugging

## Test Effettuati

La soluzione è stata testata con documenti con nomi di varia lunghezza per verificare:
- La corretta visualizzazione dei bottoni
- La gestione dei callback con nomi diretti e ID numerici
- La corretta selezione di documenti con nomi lunghi

## Lezioni Apprese

1. **Consapevolezza dei Limiti delle API**: È importante conoscere e rispettare i limiti imposti dalle API esterne
2. **Logging Dettagliato**: Un sistema di logging completo è essenziale per identificare problemi non ovviamente visibili
3. **Strategie di Fallback**: Implementare meccanismi alternativi quando i percorsi principali non sono praticabili

## Prossimi Passi

1. **Ottimizzazione della UI**: Considerare la troncatura visiva dei nomi lunghi nei bottoni
2. **Caching**: Implementare un sistema di caching per i documenti recuperati per ID numerico
3. **Monitoraggio**: Verificare l'uso di callback numerici per identificare documenti con nomi problematici

## Conclusione

La soluzione implementata risolve efficacemente il problema dei nomi documenti lunghi che superano il limite di 64 byte del campo `callback_data` dell'API Telegram. Utilizzando un sistema di fallback basato sull'ID numerico del documento, garantiamo che gli utenti possano selezionare qualsiasi documento, indipendentemente dalla lunghezza del suo nome.
