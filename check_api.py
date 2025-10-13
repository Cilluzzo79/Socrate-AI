"""
Questo script verifica quali metodi e parametri sono supportati dalla classe MemvidEncoder.
"""
import inspect
import sys

def main():
    try:
        # Importa Memvid
        try:
            from memvid import MemvidEncoder
        except ImportError as e:
            print(f"ERRORE: {e}")
            print("Assicurati che memvid sia installato con: pip install memvid")
            return 1
        
        print("\n=== Analisi API di MemvidEncoder ===\n")
        
        # Crea un'istanza
        encoder = MemvidEncoder()
        
        # Ottieni tutti i metodi disponibili
        methods = [method for method in dir(encoder) if callable(getattr(encoder, method)) and not method.startswith('_')]
        
        print("Metodi disponibili:")
        for method in sorted(methods):
            method_obj = getattr(encoder, method)
            signature = inspect.signature(method_obj)
            print(f"  - {method}{signature}")
        
        # Test specifici
        print("\nTest di compatibilità parametri:")
        
        # Test add_chunks
        try:
            encoder.add_chunks(["Test"])
            print("  ✅ add_chunks([...]) funziona")
        except Exception as e:
            print(f"  ❌ add_chunks([...]) errore: {e}")
            
        try:
            encoder.add_chunks(["Test"], source="test")
            print("  ✅ add_chunks([...], source=...) funziona")
        except Exception as e:
            print(f"  ❌ add_chunks([...], source=...) errore: {e}")
            
        # Test add_text
        try:
            encoder.add_text("Test")
            print("  ✅ add_text(...) funziona")
        except Exception as e:
            print(f"  ❌ add_text(...) errore: {e}")
            
        try:
            encoder.add_text("Test", source="test")
            print("  ✅ add_text(..., source=...) funziona")
        except Exception as e:
            print(f"  ❌ add_text(..., source=...) errore: {e}")
        
        print("\nAnalisi completata.\n")
        return 0
        
    except Exception as e:
        import traceback
        print(f"\nERRORE: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
