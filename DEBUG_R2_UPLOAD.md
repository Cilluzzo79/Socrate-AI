# Debug R2 Upload Error

## Problema
Upload to cloud storage failed - L'upload su Cloudflare R2 sta fallendo

## Passi per Diagnosticare

### 1. Verifica Variabili d'Ambiente su Railway

Vai su Railway → Web Service → Variables e verifica che esistano:

```
R2_ACCESS_KEY_ID=<la tua access key>
R2_SECRET_ACCESS_KEY=<la tua secret key>
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
R2_BUCKET_NAME=socrate-ai-storage
```

**IMPORTANTE**: Verifica che:
- Non ci siano spazi prima/dopo i valori
- Non ci siano caratteri speciali nascosti
- Le chiavi siano quelle S3-compatible (non API tokens normali)

### 2. Verifica i Log del Web Service

Su Railway → Web Service → Deployments → Logs, cerca:

```
Initializing S3 client for R2...
  R2_ACCESS_KEY_ID: SET
  R2_SECRET_ACCESS_KEY: SET
  R2_ENDPOINT_URL: https://...
  R2_BUCKET_NAME: socrate-ai-storage
✅ S3 client initialized successfully
```

Se vedi "MISSING" accanto a qualche variabile, quella variabile non è configurata.

### 3. Verifica il Bucket su Cloudflare

1. Vai su Cloudflare Dashboard → R2
2. Verifica che il bucket `socrate-ai-storage` esista
3. Verifica che il token S3 abbia permessi di READ e WRITE

### 4. Test Locale (Opzionale)

Se vuoi testare in locale, esporta le variabili:

```bash
# Windows PowerShell
$env:R2_ACCESS_KEY_ID="<tua_access_key>"
$env:R2_SECRET_ACCESS_KEY="<tua_secret_key>"
$env:R2_ENDPOINT_URL="https://<account_id>.r2.cloudflarestorage.com"
$env:R2_BUCKET_NAME="socrate-ai-storage"

# Esegui test
python test_r2_connection.py
```

Lo script di test ti dirà esattamente dove sta fallendo.

## Errori Comuni

### Errore 1: "R2 credentials not configured"
**Causa**: Variabili d'ambiente mancanti
**Soluzione**:
- Vai su Railway → Web Service → Variables
- Aggiungi tutte e 4 le variabili R2
- Riavvia il servizio (Railway redeploy automatico)

### Errore 2: "InvalidAccessKeyId"
**Causa**: R2_ACCESS_KEY_ID non valida
**Soluzione**:
- Vai su Cloudflare R2 → API Tokens
- Verifica che il token esista e sia S3-compatible
- Se necessario, genera nuovo token S3-compatible
- Aggiorna R2_ACCESS_KEY_ID su Railway

### Errore 3: "SignatureDoesNotMatch"
**Causa**: R2_SECRET_ACCESS_KEY non corretta
**Soluzione**:
- Rigenera il token S3-compatible su Cloudflare
- Aggiorna R2_SECRET_ACCESS_KEY su Railway
- ATTENZIONE: Non confondere con i token API normali

### Errore 4: "NoSuchBucket"
**Causa**: Il bucket 'socrate-ai-storage' non esiste
**Soluzione**:
- Vai su Cloudflare R2 → Create bucket
- Nome: `socrate-ai-storage`
- Region: Europe (se vuoi GDPR compliance)

### Errore 5: "AccessDenied"
**Causa**: Il token S3 non ha permessi write
**Soluzione**:
- Vai su Cloudflare R2 → API Tokens
- Modifica il token
- Assicurati che "Object Read & Write" sia selezionato
- Applica al bucket `socrate-ai-storage`

## Log Dettagliati

Con le modifiche apportate, ora vedrai nei log esattamente:

```
R2 ClientError uploading 'users/xxx/docs/yyy/file.pdf': [CODICE_ERRORE] - [MESSAGGIO]
```

I codici errore più comuni:
- `InvalidAccessKeyId` → Access key sbagliata
- `SignatureDoesNotMatch` → Secret key sbagliata
- `NoSuchBucket` → Bucket non esiste
- `AccessDenied` → Permessi insufficienti
- `InvalidRequest` → Endpoint URL sbagliato

## Checklist Verifica

- [ ] Bucket `socrate-ai-storage` esiste su Cloudflare R2
- [ ] Token S3-compatible creato (non token API normale)
- [ ] Token ha permessi "Object Read & Write"
- [ ] Token applicato al bucket corretto
- [ ] Tutte e 4 le variabili impostate su Railway Web Service
- [ ] Nessuno spazio o carattere nascosto nelle variabili
- [ ] Endpoint URL è nel formato: `https://<account_id>.r2.cloudflarestorage.com`
- [ ] Servizio riavviato dopo aver aggiunto le variabili

## Prossimi Passi

1. **Controlla i log Railway** per vedere il messaggio di errore specifico
2. **Verifica le variabili** su Railway (copia-incolla per evitare typo)
3. **Se necessario**, rigenera i token S3 su Cloudflare
4. **Testa con** `python test_r2_connection.py` in locale per isolare il problema

## Contatti di Supporto

- Cloudflare R2 Docs: https://developers.cloudflare.com/r2/
- Railway Docs: https://docs.railway.app/
- S3 Error Codes: https://docs.aws.amazon.com/AmazonS3/latest/API/ErrorResponses.html
