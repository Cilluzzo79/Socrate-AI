# Soluzione al Problema di Nomi File Lunghi in Telegram

Ho identificato e risolto il problema che causava l'errore nella selezione dei documenti. L'analisi del log di debug ha evidenziato un'importante limitazione tecnica:

## Il problema: Limite di callback_data in Telegram

```
ATTENZIONE: callback_data troppo lungo! (69 caratteri)
```

Telegram impone un limite di **64 byte** per il campo `callback_data` dei pulsanti inline. Il file con nome lungo "mind_magic_the_neuroscience_of_manifestation_and_how_it_changes 2" superava questo limite quando combinato con il prefisso "doc:", raggiungendo 69 caratteri.

## Soluzione implementata

Ho modificato il codice per gestire in modo intelligente i nomi lunghi:

1. **Uso di ID numerico per nomi lunghi**:
   ```python
   if len(doc_pattern + callback_id) > 60:  # Margine di sicurezza
       # Utilizzo dell'ID numerico interno invece del nome completo
       callback_id = f"id:{doc.id}"
   ```

2. **Gestione dei callback con ID numerico**:
   Ho aggiornato il gestore di callback per riconoscere e gestire correttamente sia i riferimenti diretti che quelli numerici.

3. **Miglioramento della formattazione**:
   Migliorata la visualizzazione delle dimensioni dei file (MB o KB a seconda della grandezza).

4. **Gestione degli errori robusta**:
   Aggiunta una gestione degli errori completa con logging dettagliato.

## Vantaggi della soluzione

- **Compatibilità completa**: Rispetta il limite di 64 byte di Telegram
- **Esperienza utente inalterata**: L'utente vede ancora il nome completo del documento
- **Robustezza**: Gestione completa di errori e casi limite
- **Diagnostica migliorata**: Logging dettagliato per futuri debug

## Come verificare la soluzione

1. **Riavvia il bot**:
   ```
   start_bot.bat
   ```

2. **Prova a selezionare documenti**:
   Usa il comando `/select` nel bot Telegram e verifica che tutti i documenti siano ora selezionabili, incluso quello con il nome lungo.

3. **Verifica i log**:
   Se necessario, controlla i file di log nella cartella "logs" per ulteriori dettagli sul comportamento del sistema.

Questa soluzione affronta la causa principale del problema e dovrebbe rendere il sistema completamente funzionante, indipendentemente dalla lunghezza dei nomi dei file Memvid.
