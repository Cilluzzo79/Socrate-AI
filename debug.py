#!/usr/bin/env python
"""
Script di diagnostica per verificare che l'ambiente sia correttamente configurato
per l'applicazione Memvid Document Encoder.
"""
import os
import sys
import platform
import importlib.util

def check_module(module_name):
    """Verifica se un modulo è installato e restituisce informazioni su di esso."""
    spec = importlib.util.find_spec(module_name)
    if spec is not None:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        version = getattr(module, "__version__", "Versione sconosciuta")
        location = getattr(module, "__file__", "Percorso sconosciuto")
        return True, version, location
    return False, None, None

def main():
    """Esegue la diagnostica completa."""
    print("\n===== DIAGNOSTICA MEMVID DOCUMENT ENCODER =====\n")
    
    # Informazioni di sistema
    print("Informazioni di sistema:")
    print(f"  Sistema operativo: {platform.system()} {platform.release()}")
    print(f"  Python versione: {platform.python_version()}")
    print(f"  Directory corrente: {os.getcwd()}")
    
    # Verifica delle cartelle
    base_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"\nDirectory del progetto: {base_dir}")
    
    print("\nStrutttura delle cartelle:")
    for item in os.listdir(base_dir):
        path = os.path.join(base_dir, item)
        if os.path.isdir(path):
            print(f"  [DIR] {item}")
        else:
            print(f"  [FILE] {item}")
    
    # Verifica delle dipendenze
    print("\nVerifica delle dipendenze:")
    dependencies = [
        "memvid", 
        "gradio", 
        "qrcode", 
        "PIL", 
        "cv2", 
        "pyzbar", 
        "sentence_transformers", 
        "numpy", 
        "PyPDF2"
    ]
    
    all_ok = True
    for dep in dependencies:
        is_installed, version, location = check_module(dep)
        if is_installed:
            print(f"  ✅ {dep}: {version} ({location})")
        else:
            print(f"  ❌ {dep}: NON INSTALLATO")
            all_ok = False
    
    if all_ok:
        print("\n✅ Tutte le dipendenze sono installate correttamente!")
        print("\nPuoi avviare l'applicazione con: python run.py")
    else:
        print("\n❌ Alcune dipendenze sono mancanti.")
        print("Installa tutte le dipendenze con: pip install -r requirements.txt")
    
    print("\n=================================================\n")
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
