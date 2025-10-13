"""
Quick Test Script for Memvid Verifier
======================================

Script veloce per testare il verificatore su file di esempio.
Utile per verificare che tutto funzioni correttamente.
"""

from verify_memvid import MemvidVerifier
from pathlib import Path


def test_single_file():
    """Test su un singolo file (se esiste)"""
    print("\n🧪 TEST VERIFICA SINGOLO FILE")
    print("="*70)
    
    # Cerca un file di esempio
    uploads_dir = Path("uploads")
    outputs_dir = Path("outputs")
    
    if not uploads_dir.exists() or not outputs_dir.exists():
        print("❌ Directory uploads o outputs non trovate")
        print("💡 Crea le directory e aggiungi file di test")
        return False
    
    # Trova primo PDF/TXT
    source_file = None
    for ext in ['.pdf', '.txt', '.md']:
        files = list(uploads_dir.glob(f"*{ext}"))
        if files:
            source_file = files[0]
            break
    
    if not source_file:
        print("❌ Nessun file sorgente trovato in uploads/")
        print("💡 Aggiungi un file .pdf, .txt o .md per testare")
        return False
    
    # Cerca JSON corrispondente
    json_file = outputs_dir / f"{source_file.stem}.json"
    
    if not json_file.exists():
        print(f"❌ File JSON non trovato: {json_file.name}")
        print(f"💡 Genera prima il file Memvid da {source_file.name}")
        return False
    
    print(f"\n✅ File trovati:")
    print(f"   Sorgente: {source_file.name}")
    print(f"   JSON:     {json_file.name}")
    
    # Verifica
    try:
        verifier = MemvidVerifier(source_file, json_file)
        result = verifier.verify(verbose=True, check_hash=False)
        
        if result and result['evaluation']['is_complete']:
            print("\n✅ TEST PASSATO: File completo!")
            return True
        else:
            print("\n⚠️  TEST PARZIALE: File verificato ma incompleto")
            return True
    
    except Exception as e:
        print(f"\n❌ TEST FALLITO: {e}")
        return False


def test_imports():
    """Test che tutte le librerie necessarie siano installate"""
    print("\n🧪 TEST IMPORTAZIONI")
    print("="*70)
    
    errors = []
    
    # Test PyPDF2
    try:
        import PyPDF2
        print("✅ PyPDF2 installato")
    except ImportError:
        errors.append("PyPDF2")
        print("❌ PyPDF2 NON installato")
    
    # Test json (built-in)
    try:
        import json
        print("✅ json disponibile")
    except ImportError:
        errors.append("json")
        print("❌ json NON disponibile")
    
    # Test pathlib (built-in)
    try:
        from pathlib import Path
        print("✅ pathlib disponibile")
    except ImportError:
        errors.append("pathlib")
        print("❌ pathlib NON disponibile")
    
    # Test hashlib (built-in)
    try:
        import hashlib
        print("✅ hashlib disponibile")
    except ImportError:
        errors.append("hashlib")
        print("❌ hashlib NON disponibile")
    
    if errors:
        print(f"\n❌ Librerie mancanti: {', '.join(errors)}")
        print("\n💡 Installa con:")
        print("   pip install PyPDF2")
        return False
    else:
        print("\n✅ Tutte le librerie necessarie sono installate!")
        return True


def test_file_structure():
    """Test struttura directory"""
    print("\n🧪 TEST STRUTTURA DIRECTORY")
    print("="*70)
    
    uploads_dir = Path("uploads")
    outputs_dir = Path("outputs")
    
    issues = []
    
    # Check uploads
    if not uploads_dir.exists():
        issues.append("Directory 'uploads' non esiste")
        print("❌ uploads/ NON esiste")
    else:
        pdf_count = len(list(uploads_dir.glob("*.pdf")))
        txt_count = len(list(uploads_dir.glob("*.txt")))
        md_count = len(list(uploads_dir.glob("*.md")))
        total = pdf_count + txt_count + md_count
        
        print(f"✅ uploads/ esiste")
        print(f"   • File PDF: {pdf_count}")
        print(f"   • File TXT: {txt_count}")
        print(f"   • File MD:  {md_count}")
        print(f"   • Totale:   {total}")
        
        if total == 0:
            issues.append("Nessun file sorgente in uploads/")
    
    # Check outputs
    if not outputs_dir.exists():
        issues.append("Directory 'outputs' non esiste")
        print("❌ outputs/ NON esiste")
    else:
        json_count = len(list(outputs_dir.glob("*.json")))
        mp4_count = len(list(outputs_dir.glob("*.mp4")))
        
        print(f"✅ outputs/ esiste")
        print(f"   • File JSON: {json_count}")
        print(f"   • File MP4:  {mp4_count}")
        
        if json_count == 0:
            issues.append("Nessun file JSON in outputs/")
    
    if issues:
        print(f"\n⚠️  Problemi trovati:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n💡 Suggerimenti:")
        print("   1. Crea directory: mkdir uploads outputs")
        print("   2. Metti file sorgente in uploads/")
        print("   3. Genera file Memvid con encoder")
        return False
    else:
        print("\n✅ Struttura directory corretta!")
        return True


def main():
    """Esegue tutti i test"""
    print("\n" + "="*70)
    print("   🧪 MEMVID VERIFIER - TEST SUITE")
    print("   Verifica rapida che tutto sia configurato correttamente")
    print("="*70)
    
    results = {
        'imports': False,
        'structure': False,
        'verification': False
    }
    
    # Test 1: Importazioni
    results['imports'] = test_imports()
    
    if not results['imports']:
        print("\n❌ TEST FALLITO: Installa librerie mancanti")
        print("   pip install PyPDF2")
        return
    
    # Test 2: Struttura
    results['structure'] = test_file_structure()
    
    if not results['structure']:
        print("\n⚠️  Configura struttura directory prima di continuare")
    
    # Test 3: Verifica (solo se struttura OK)
    if results['structure']:
        results['verification'] = test_single_file()
    
    # Riepilogo
    print("\n" + "="*70)
    print("📊 RIEPILOGO TEST")
    print("="*70)
    
    for test_name, passed in results.items():
        emoji = "✅" if passed else "❌"
        status = "PASSATO" if passed else "FALLITO"
        print(f"{emoji} {test_name.upper():<15} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 TUTTI I TEST PASSATI!")
        print("   Il sistema è pronto per verificare file Memvid")
        print("\n💡 Prossimi step:")
        print("   • Usa: python verify_memvid.py <pdf> <json>")
        print("   • Oppure: python verify_batch.py")
        print("   • Oppure: run_verify.bat (Windows)")
    else:
        print("\n⚠️  ALCUNI TEST FALLITI")
        print("   Risolvi i problemi sopra e riprova")
    
    print("="*70)


if __name__ == "__main__":
    main()
