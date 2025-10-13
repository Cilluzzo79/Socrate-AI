"""
Memvid Batch Verifier
=====================

Script per verificare più file Memvid in batch e generare un report completo.

Uso:
    python verify_batch.py
    
Il script cerca automaticamente tutti i file nella cartella outputs/ e li verifica.
Genera un report dettagliato in formato JSON e tabella console.

Output:
    - Tabella riassuntiva di tutti i file
    - Report dettagliato JSON
    - Statistiche aggregate
"""

import json
from pathlib import Path
from datetime import datetime
from verify_memvid import MemvidVerifier
import sys


class BatchVerifier:
    """Classe per verifica batch di file Memvid"""
    
    def __init__(self, uploads_dir="uploads", outputs_dir="outputs"):
        """
        Inizializza batch verifier
        
        Args:
            uploads_dir: Directory dei file sorgente
            outputs_dir: Directory dei file Memvid generati
        """
        self.uploads_dir = Path(uploads_dir)
        self.outputs_dir = Path(outputs_dir)
        
        if not self.uploads_dir.exists():
            print(f"⚠️  Directory uploads non trovata: {uploads_dir}")
        if not self.outputs_dir.exists():
            print(f"⚠️  Directory outputs non trovata: {outputs_dir}")
    
    def find_file_pairs(self):
        """
        Trova coppie di file sorgente-JSON
        
        Returns:
            list: Lista di tuple (source_path, json_path)
        """
        pairs = []
        
        # Trova tutti i JSON in outputs
        json_files = list(self.outputs_dir.glob("*.json"))
        
        # Filtra solo i file _index.json (esclude _metadata.json)
        json_files = [f for f in json_files if '_index.json' in f.name]
        
        for json_file in json_files:
            # Rimuovi suffissi comuni per trovare il nome base
            base_name = json_file.stem
            
            # Rimuovi suffissi: _sections_index, _index, _smart_index, _light_index
            for suffix in ['_sections_index', '_smart_index', '_light_index', '_index']:
                if base_name.endswith(suffix):
                    base_name = base_name[:-len(suffix)]
                    break
            
            # Cerca PDF
            pdf_path = self.uploads_dir / f"{base_name}.pdf"
            if pdf_path.exists():
                pairs.append((pdf_path, json_file))
                continue
            
            # Cerca TXT
            txt_path = self.uploads_dir / f"{base_name}.txt"
            if txt_path.exists():
                pairs.append((txt_path, json_file))
                continue
            
            # Cerca MD
            md_path = self.uploads_dir / f"{base_name}.md"
            if md_path.exists():
                pairs.append((md_path, json_file))
                continue
            
            print(f"⚠️  Nessun file sorgente trovato per: {json_file.name}")
            print(f"   Nome base cercato: {base_name}.pdf/txt/md")
        
        return pairs
    
    def verify_all(self, verbose=True):
        """
        Verifica tutti i file trovati
        
        Args:
            verbose: Se True, mostra output dettagliato
        
        Returns:
            dict: Risultati aggregati
        """
        pairs = self.find_file_pairs()
        
        if not pairs:
            print("\n❌ Nessuna coppia di file trovata!")
            print("💡 Assicurati che:")
            print("   • I file sorgente siano in 'uploads/'")
            print("   • I file JSON siano in 'outputs/'")
            print("   • I nomi dei file corrispondano (esclusa estensione)")
            return None
        
        if verbose:
            print("\n" + "="*80)
            print("🔍 VERIFICA BATCH MEMVID")
            print("="*80)
            print(f"\n📁 Directory uploads: {self.uploads_dir}")
            print(f"📁 Directory outputs: {self.outputs_dir}")
            print(f"\n📊 Trovate {len(pairs)} coppie di file da verificare")
            print("-"*80)
        
        results = []
        
        for i, (source_path, json_path) in enumerate(pairs, 1):
            if verbose:
                print(f"\n{'='*80}")
                print(f"📄 [{i}/{len(pairs)}] {source_path.name} → {json_path.name}")
                print(f"{'='*80}")
            
            try:
                verifier = MemvidVerifier(source_path, json_path)
                result = verifier.verify(verbose=verbose, check_hash=False)
                
                if result:
                    results.append(result)
                else:
                    print(f"❌ Verifica fallita per {source_path.name}")
            
            except Exception as e:
                print(f"❌ ERRORE su {source_path.name}: {e}")
                continue
        
        # Genera statistiche aggregate
        if verbose and results:
            self._print_summary(results)
        
        return results
    
    def _print_summary(self, results):
        """Stampa tabella riassuntiva"""
        print("\n" + "="*80)
        print("📊 RIEPILOGO VERIFICA BATCH")
        print("="*80)
        
        # Header tabella
        print(f"\n{'File':<30} {'Parole':>12} {'Copertura':>10} {'Rating':<15}")
        print("-"*80)
        
        # Righe
        for result in results:
            filename = Path(result['source_file']).stem[:28]
            words = result['statistics']['json_words']
            coverage = result['coverage']['word_percentage']
            rating = result['evaluation']['rating']
            
            # Emoji basato su rating
            emoji = {
                'ECCELLENTE': '✅',
                'OTTIMO': '✅',
                'BUONO': '⚠️',
                'SUFFICIENTE': '⚠️',
                'INSUFFICIENTE': '❌'
            }.get(rating, '❓')
            
            print(f"{emoji} {filename:<28} {words:>12,} {coverage:>9.1f}% {rating:<15}")
        
        # Statistiche aggregate
        print("-"*80)
        
        total_files = len(results)
        complete_files = sum(1 for r in results if r['evaluation']['is_complete'])
        avg_coverage = sum(r['coverage']['word_percentage'] for r in results) / total_files
        
        print(f"\n📈 STATISTICHE AGGREGATE:")
        print(f"   • File totali:         {total_files}")
        print(f"   • File completi:       {complete_files} ({complete_files/total_files*100:.1f}%)")
        print(f"   • File incompleti:     {total_files - complete_files}")
        print(f"   • Copertura media:     {avg_coverage:.2f}%")
        
        # Distribuzione rating
        rating_counts = {}
        for r in results:
            rating = r['evaluation']['rating']
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
        
        print(f"\n🏆 DISTRIBUZIONE RATING:")
        for rating, count in sorted(rating_counts.items(), key=lambda x: x[1], reverse=True):
            emoji = {
                'ECCELLENTE': '✅',
                'OTTIMO': '✅',
                'BUONO': '⚠️',
                'SUFFICIENTE': '⚠️',
                'INSUFFICIENTE': '❌'
            }.get(rating, '❓')
            print(f"   {emoji} {rating:<15} {count:>3} file ({count/total_files*100:.1f}%)")
        
        print("="*80)
    
    def save_report(self, results, output_path=None):
        """
        Salva report in formato JSON
        
        Args:
            results: Lista di risultati da salvare
            output_path: Path dove salvare (opzionale)
        
        Returns:
            Path: Path del file salvato
        """
        if not results:
            print("⚠️  Nessun risultato da salvare")
            return None
        
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.outputs_dir / f"batch_verification_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'uploads_dir': str(self.uploads_dir),
            'outputs_dir': str(self.outputs_dir),
            'total_files': len(results),
            'summary': {
                'complete_files': sum(1 for r in results if r['evaluation']['is_complete']),
                'incomplete_files': sum(1 for r in results if not r['evaluation']['is_complete']),
                'avg_coverage': sum(r['coverage']['word_percentage'] for r in results) / len(results)
            },
            'results': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Report salvato: {output_path}")
        print(f"   Dimensione: {output_path.stat().st_size / 1024:.1f} KB")
        
        return output_path


def main():
    """Main function per uso da command line"""
    
    # Banner
    print("\n" + "="*80)
    print("   🔍 MEMVID BATCH VERIFIER")
    print("   Verifica automatica di tutti i file Memvid")
    print("="*80)
    
    # Parse arguments
    uploads_dir = "uploads"
    outputs_dir = "outputs"
    save_report = True
    
    if '--uploads' in sys.argv:
        idx = sys.argv.index('--uploads')
        if idx + 1 < len(sys.argv):
            uploads_dir = sys.argv[idx + 1]
    
    if '--outputs' in sys.argv:
        idx = sys.argv.index('--outputs')
        if idx + 1 < len(sys.argv):
            outputs_dir = sys.argv[idx + 1]
    
    if '--no-save' in sys.argv:
        save_report = False
    
    # Crea verifier
    verifier = BatchVerifier(uploads_dir, outputs_dir)
    
    # Esegui verifica
    results = verifier.verify_all(verbose=True)
    
    if results is None or not results:
        print("\n❌ Verifica batch fallita")
        sys.exit(1)
    
    # Salva report
    if save_report:
        verifier.save_report(results)
    
    # Exit code basato su file completi
    complete_count = sum(1 for r in results if r['evaluation']['is_complete'])
    total_count = len(results)
    
    if complete_count == total_count:
        print(f"\n✅ Tutti i {total_count} file sono completi!")
        sys.exit(0)
    elif complete_count > total_count / 2:
        print(f"\n⚠️  {complete_count}/{total_count} file completi")
        sys.exit(0)
    else:
        print(f"\n❌ Solo {complete_count}/{total_count} file completi")
        sys.exit(1)


if __name__ == "__main__":
    main()
