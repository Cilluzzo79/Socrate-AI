"""
Analizza struttura JSON Memvid per debugging
"""
import json
from pathlib import Path

json_path = Path("outputs/TUIR 2025_sections_index.json")

print("📊 ANALISI STRUTTURA JSON MEMVID")
print("="*70)
print(f"File: {json_path.name}")
print(f"Dimensione: {json_path.stat().st_size / 1024:.1f} KB")
print()

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Tipo dato principale:", type(data).__name__)
print()

if isinstance(data, list):
    print(f"È un array con {len(data)} elementi")
    print()
    
    if len(data) > 0:
        print("Primo elemento:")
        print(json.dumps(data[0], indent=2, ensure_ascii=False)[:1000])
        print()
        
        # Conta elementi con 'text'
        with_text = sum(1 for item in data if isinstance(item, dict) and 'text' in item)
        print(f"Elementi con campo 'text': {with_text}")
        
        if with_text > 0:
            # Mostra primo elemento con text
            for item in data:
                if isinstance(item, dict) and 'text' in item:
                    print(f"\nPrimo chunk con text:")
                    print(f"  Lunghezza testo: {len(item['text'])} caratteri")
                    print(f"  Prime 200 char: {item['text'][:200]}")
                    break

elif isinstance(data, dict):
    print(f"È un dizionario con chiavi: {list(data.keys())}")
    print()
    
    if 'chunks' in data:
        print(f"Ha campo 'chunks' con {len(data['chunks'])} elementi")
        if len(data['chunks']) > 0:
            print("\nPrimo chunk:")
            print(json.dumps(data['chunks'][0], indent=2, ensure_ascii=False)[:500])
    
    # Cerca altri campi con testo
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0:
            print(f"\nCampo '{key}': array con {len(value)} elementi")
            print(f"Primo elemento: {str(value[0])[:200]}")
