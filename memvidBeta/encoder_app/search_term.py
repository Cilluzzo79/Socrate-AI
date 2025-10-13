"""
Conta occorrenze termine in documento Memvid
"""
import json
from pathlib import Path
import re

# File da analizzare
json_path = Path("outputs/Frammenti di un insegnamento sconosciuto_sections_index.json")
search_term = "carboni"  # Cerchiamo anche carbonio, carboni, etc

print("🔍 RICERCA TERMINE NEL DOCUMENTO")
print("="*70)
print(f"File: {json_path.name}")
print(f"Termine: '{search_term}' (case-insensitive)")
print()

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Estrai chunks
if 'metadata' in data:
    chunks = data['metadata']
else:
    chunks = data.get('chunks', [])

print(f"Totale chunks: {len(chunks)}")
print()

# Cerca termine
matches = []
for i, chunk in enumerate(chunks):
    if 'text' not in chunk:
        continue
    
    text = chunk['text'].lower()
    
    # Conta occorrenze
    count = len(re.findall(r'\bcarbon[oi]\w*', text, re.IGNORECASE))
    
    if count > 0:
        # Estrai contesto (200 char prima e dopo)
        positions = [m.start() for m in re.finditer(r'\bcarbon[oi]\w*', text, re.IGNORECASE)]
        
        for pos in positions:
            start = max(0, pos - 200)
            end = min(len(text), pos + 200)
            context = text[start:end]
            
            matches.append({
                'chunk_id': i,
                'position': pos,
                'context': context,
                'full_text': chunk['text']
            })

print(f"📊 RISULTATI:")
print(f"   Occorrenze totali: {len(matches)}")
print(f"   Chunks contenenti il termine: {len(set(m['chunk_id'] for m in matches))}")
print()

if matches:
    print("📄 OCCORRENZE TROVATE:")
    print("-"*70)
    
    for i, match in enumerate(matches[:10], 1):  # Prime 10
        print(f"\n{i}. Chunk #{match['chunk_id']} - Posizione {match['position']}")
        print(f"   Contesto: ...{match['context']}...")
        
        # Cerca numero pagina
        page_match = re.search(r'## Pagina (\d+)', match['full_text'])
        if page_match:
            print(f"   📄 Pagina: {page_match.group(1)}")
        
        print()
    
    if len(matches) > 10:
        print(f"\n... e altre {len(matches) - 10} occorrenze")
else:
    print("❌ Nessuna occorrenza trovata!")

print("="*70)
