import os
import json

# Test scrittura file nella cartella outputs
output_dir = r"D:\railway\memvid\memvidBeta\encoder_app\outputs"
test_file = os.path.join(output_dir, "Adler_sections_metadata.json")

print(f"Tentativo di creare: {test_file}")
print(f"Directory esiste: {os.path.exists(output_dir)}")
print(f"File esiste giÃ : {os.path.exists(test_file)}")

try:
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump({"test": "data"}, f, indent=2)
    print("✅ SUCCESSO! File creato correttamente")
    
    # Verifica
    if os.path.exists(test_file):
        print(f"✅ File verificato: {test_file}")
        size = os.path.getsize(test_file)
        print(f"   Dimensione: {size} bytes")
    
except Exception as e:
    print(f"❌ ERRORE: {e}")
    import traceback
    traceback.print_exc()
