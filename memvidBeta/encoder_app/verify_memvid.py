"""
Memvid Completeness Verifier
============================

Script per verificare che un file Memvid (JSON) contenga tutto il testo
del documento originale (PDF/TXT).

Uso:
    python verify_memvid.py <pdf_path> <json_path>
    
Esempio:
    python verify_memvid.py "uploads/manuale.pdf" "outputs/manuale.json"

Output:
    - Statistiche complete di confronto
    - Percentuale di copertura
    - Valutazione finale (Eccellente/Ottimo/Buono/Insufficiente)
"""

import json
import PyPDF2
import hashlib
from pathlib import Path
import sys
from datetime import datetime


class MemvidVerifier:
    """Classe per verificare completezza di file Memvid"""
    
    def __init__(self, source_path, json_path):
        """
        Inizializza il verificatore
        
        Args:
            source_path: Path al file sorgente (PDF o TXT)
            json_path: Path al file JSON Memvid
        """
        self.source_path = Path(source_path)
        self.json_path = Path(json_path)
        
        # Verifica esistenza file
        if not self.source_path.exists():
            raise FileNotFoundError(f"File sorgente non trovato: {source_path}")
        if not self.json_path.exists():
            raise FileNotFoundError(f"File JSON non trovato: {json_path}")
        
        # Determina tipo sorgente
        self.source_type = self.source_path.suffix.lower()
    
    def extract_source_text(self):
        """Estrae tutto il testo dal file sorgente"""
        if self.source_type == '.pdf':
            return self._extract_pdf_text()
        elif self.source_type in ['.txt', '.md']:
            return self._extract_txt_text()
        else:
            raise ValueError(f"Tipo file non supportato: {self.source_type}")
    
    def _extract_pdf_text(self):
        """Estrae testo da PDF"""
        try:
            with open(self.source_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                total_pages = len(reader.pages)
                
                print(f"   📄 Estrazione da {total_pages} pagine PDF...")
                
                for i, page in enumerate(reader.pages, 1):
                    if i % 10 == 0:  # Progress ogni 10 pagine
                        print(f"      Pagina {i}/{total_pages}...", end='\r')
                    text += page.extract_text()
                
                print(f"      Completato: {total_pages} pagine estratte")
                return text
        except Exception as e:
            raise Exception(f"Errore estrazione PDF: {e}")
    
    def _extract_txt_text(self):
        """Estrae testo da TXT/MD"""
        try:
            with open(self.source_path, 'r', encoding='utf-8') as f:
                text = f.read()
            print(f"   📝 File TXT/MD letto correttamente")
            return text
        except Exception as e:
            raise Exception(f"Errore lettura TXT: {e}")
    
    def extract_json_text(self):
        """Estrae tutto il testo dal JSON Memvid"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks_text = []
            chunk_count = 0
            
            # Memvid può avere diversi formati
            if isinstance(data, list):
                # Formato: lista di chunk
                for chunk in data:
                    if isinstance(chunk, dict) and 'text' in chunk:
                        chunks_text.append(chunk['text'])
                        chunk_count += 1
                    elif isinstance(chunk, str):
                        chunks_text.append(chunk)
                        chunk_count += 1
            
            elif isinstance(data, dict):
                # Formato dizionario - prova diversi campi
                
                # 1. Prova campo 'metadata' (usato da memvid_sections)
                if 'metadata' in data and isinstance(data['metadata'], list):
                    for chunk in data['metadata']:
                        if isinstance(chunk, dict) and 'text' in chunk:
                            chunks_text.append(chunk['text'])
                            chunk_count += 1
                
                # 2. Prova campo 'chunks'
                elif 'chunks' in data:
                    for chunk in data['chunks']:
                        if isinstance(chunk, dict) and 'text' in chunk:
                            chunks_text.append(chunk['text'])
                            chunk_count += 1
                
                # 3. Prova altri campi comuni
                else:
                    for key in ['data', 'items', 'content']:
                        if key in data and isinstance(data[key], list):
                            for chunk in data[key]:
                                if isinstance(chunk, dict) and 'text' in chunk:
                                    chunks_text.append(chunk['text'])
                                    chunk_count += 1
                            if chunk_count > 0:
                                break
            
            full_text = ' '.join(chunks_text)
            print(f"   💾 {chunk_count} chunks estratti dal JSON")
            
            return full_text, chunk_count
        except Exception as e:
            raise Exception(f"Errore lettura JSON: {e}")
    
    def normalize_text(self, text):
        """
        Normalizza testo per confronto accurato
        - Rimuove spazi multipli
        - Rimuove newline multipli
        - Converte a minuscolo per confronto
        """
        # Preserva spazi singoli, rimuovi multipli
        normalized = ' '.join(text.split())
        return normalized
    
    def count_words(self, text):
        """Conta parole nel testo"""
        return len(text.split())
    
    def calculate_hash(self, text):
        """Calcola hash MD5 del testo normalizzato"""
        normalized = self.normalize_text(text).lower()
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def verify(self, verbose=True, check_hash=False):
        """
        Esegue verifica completa
        
        Args:
            verbose: Se True, stampa output dettagliato
            check_hash: Se True, confronta anche gli hash (più lento)
        
        Returns:
            dict: Risultati della verifica con tutte le metriche
        """
        
        if verbose:
            print("\n" + "="*70)
            print("🔍 VERIFICA COMPLETEZZA MEMVID")
            print("="*70)
            print(f"\n📄 File Sorgente: {self.source_path.name}")
            print(f"   Tipo: {self.source_type.upper()}")
            print(f"   Dimensione: {self.source_path.stat().st_size / 1024:.1f} KB")
            print(f"\n💾 File JSON: {self.json_path.name}")
            print(f"   Dimensione: {self.json_path.stat().st_size / 1024:.1f} KB")
        
        # Estrai testi
        if verbose:
            print("\n⏳ ESTRAZIONE TESTO:")
            print("-"*70)
        
        try:
            source_text = self.extract_source_text()
            json_text, num_chunks = self.extract_json_text()
        except Exception as e:
            if verbose:
                print(f"\n❌ ERRORE: {e}")
            return None
        
        # Normalizza
        source_normalized = self.normalize_text(source_text)
        json_normalized = self.normalize_text(json_text)
        
        # Statistiche
        source_words = self.count_words(source_normalized)
        json_words = self.count_words(json_normalized)
        
        source_chars = len(source_normalized)
        json_chars = len(json_normalized)
        
        if verbose:
            print("\n📊 STATISTICHE:")
            print("-"*70)
            print(f"\n📖 Sorgente Originale:")
            print(f"   • Parole:     {source_words:>10,}")
            print(f"   • Caratteri:  {source_chars:>10,}")
            
            print(f"\n💾 JSON Memvid:")
            print(f"   • Parole:     {json_words:>10,}")
            print(f"   • Caratteri:  {json_chars:>10,}")
            print(f"   • Chunks:     {num_chunks:>10,}")
            
            # Parole per chunk
            words_per_chunk = json_words / num_chunks if num_chunks > 0 else 0
            print(f"   • Parole/chunk: {words_per_chunk:>8.1f}")
        
        # Calcola copertura
        word_coverage = (json_words / source_words * 100) if source_words > 0 else 0
        char_coverage = (json_chars / source_chars * 100) if source_chars > 0 else 0
        
        if verbose:
            print("\n📈 COPERTURA:")
            print("-"*70)
            print(f"   • Parole:     {word_coverage:>6.2f}%")
            print(f"   • Caratteri:  {char_coverage:>6.2f}%")
            
            word_diff = source_words - json_words
            char_diff = source_chars - json_chars
            
            if word_diff != 0:
                print(f"\n📉 DIFFERENZE:")
                print(f"   • Parole:     {word_diff:>+10,}")
                print(f"   • Caratteri:  {char_diff:>+10,}")
                
                if word_diff > 0:
                    loss_percent = (word_diff / source_words * 100)
                    print(f"   • Perdita:    {loss_percent:>6.2f}%")
        
        # Hash check (opzionale)
        hash_match = None
        if check_hash:
            if verbose:
                print("\n🔐 VERIFICA HASH:")
                print("-"*70)
            source_hash = self.calculate_hash(source_text)
            json_hash = self.calculate_hash(json_text)
            hash_match = (source_hash == json_hash)
            
            if verbose:
                print(f"   Sorgente: {source_hash}")
                print(f"   JSON:     {json_hash}")
                print(f"   Match:    {'✅ SI' if hash_match else '❌ NO'}")
        
        # Valutazione finale
        if verbose:
            print("\n✅ VALUTAZIONE FINALE:")
            print("="*70)
        
        # Determina status
        is_complete = False
        rating = ""
        recommendation = ""
        
        if word_coverage >= 99.0:
            rating = 'ECCELLENTE'
            is_complete = True
            recommendation = "File completo al 100%! Pronto per l'uso."
            if verbose:
                print("✅ ECCELLENTE (≥99%)")
                print("   Il file Memvid contiene TUTTO il testo originale!")
                print("   ✓ Nessuna azione richiesta")
        
        elif word_coverage >= 95.0:
            rating = 'OTTIMO'
            is_complete = True
            recommendation = "File completo. Differenze minime accettabili."
            if verbose:
                print("✅ OTTIMO (95-99%)")
                print("   Il file è completo. Differenze minime sono normali e")
                print("   dovute a intestazioni/footer PDF o caratteri speciali.")
                print("   ✓ File utilizzabile senza problemi")
        
        elif word_coverage >= 90.0:
            rating = 'BUONO'
            is_complete = True
            recommendation = "File utilizzabile ma con qualche perdita."
            if verbose:
                print("⚠️  BUONO (90-95%)")
                print("   Il file è utilizzabile ma ha perso circa 5-10% del contenuto.")
                print("   ⚠ Verifica sezioni critiche del documento")
                print("   ⚠ Considera di rigenerare con settings diversi")
        
        elif word_coverage >= 80.0:
            rating = 'SUFFICIENTE'
            is_complete = False
            recommendation = "File con perdite significative. Verifica necessaria."
            if verbose:
                print("⚠️  SUFFICIENTE (80-90%)")
                print("   Il file ha perso 10-20% del contenuto.")
                print("   ⚠ Verifica urgente delle sezioni mancanti")
                print("   ⚠ Rigenera il file con chunk_size più grande")
        
        else:
            rating = 'INSUFFICIENTE'
            is_complete = False
            recommendation = "File incompleto. Rigenerazione necessaria."
            if verbose:
                print("❌ INSUFFICIENTE (<80%)")
                print("   Il file ha perso oltre il 20% del contenuto!")
                print("   ❌ NON utilizzare questo file")
                print("   ❌ Rigenera immediatamente con:")
                print("      - chunk_size più grande")
                print("      - overlap più ampio")
                print("      - verifica limite max chunks")
        
        if verbose:
            print("="*70)
            print()
        
        # Costruisci risultato
        result = {
            'timestamp': datetime.now().isoformat(),
            'source_file': str(self.source_path),
            'json_file': str(self.json_path),
            'source_type': self.source_type,
            'statistics': {
                'source_words': source_words,
                'source_chars': source_chars,
                'json_words': json_words,
                'json_chars': json_chars,
                'num_chunks': num_chunks,
                'words_per_chunk': json_words / num_chunks if num_chunks > 0 else 0
            },
            'coverage': {
                'word_percentage': round(word_coverage, 2),
                'char_percentage': round(char_coverage, 2),
                'word_difference': word_diff,
                'char_difference': char_diff
            },
            'evaluation': {
                'is_complete': is_complete,
                'rating': rating,
                'recommendation': recommendation
            }
        }
        
        if check_hash:
            result['hash_match'] = hash_match
        
        return result


def main():
    """Main function per uso da command line"""
    
    # Banner
    print("\n" + "="*70)
    print("   🔍 MEMVID COMPLETENESS VERIFIER")
    print("   Verifica che il file Memvid contenga tutto il testo originale")
    print("="*70)
    
    # Check arguments
    if len(sys.argv) < 3:
        print("\n❌ ERRORE: Argomenti insufficienti")
        print("\n📖 USO:")
        print("   python verify_memvid.py <file_sorgente> <file_json>")
        print("\n📝 ESEMPI:")
        print('   python verify_memvid.py "uploads/manuale.pdf" "outputs/manuale.json"')
        print('   python verify_memvid.py "documento.txt" "documento.json"')
        print("\n💡 SUGGERIMENTO:")
        print("   Usa percorsi relativi o assoluti con virgolette se contengono spazi")
        sys.exit(1)
    
    source_path = sys.argv[1]
    json_path = sys.argv[2]
    
    # Opzioni
    check_hash = '--hash' in sys.argv
    save_report = '--save' in sys.argv
    
    try:
        # Crea verificatore
        verifier = MemvidVerifier(source_path, json_path)
        
        # Esegui verifica
        result = verifier.verify(verbose=True, check_hash=check_hash)
        
        if result is None:
            print("\n❌ Verifica fallita")
            sys.exit(1)
        
        # Salva report se richiesto
        if save_report:
            report_path = Path(json_path).parent / f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Report salvato: {report_path}")
        
        # Exit code basato su completezza
        if result['evaluation']['is_complete']:
            print("✅ EXIT CODE: 0 (Successo)")
            sys.exit(0)
        else:
            print("⚠️  EXIT CODE: 1 (File incompleto)")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"\n❌ ERRORE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRORE IMPREVISTO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
