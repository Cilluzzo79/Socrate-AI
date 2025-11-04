"""
Test realistico ONNX Reranker - Scenario produzione con più chunks

Query: "Come si preparano le orecchiette?"
Chunks: 30 chunk misti (realistico per documento medio)
"""

import time
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_realistic_scenario():
    """Test con scenario realistico: 30 chunks, query orecchiette"""

    print("=" * 80)
    print("🍝 TEST REALISTICO ONNX - Query Orecchiette con 30 Chunks")
    print("=" * 80)
    print()

    # Import
    from core.reranker_onnx import rerank_chunks_onnx

    # 30 chunks misti - alcuni rilevanti per orecchiette, molti no
    test_chunks = [
        # RILEVANTI (chunks che dovrebbero rankare alto)
        {'text': 'Le orecchiette sono una pasta tipica pugliese a forma di piccole orecchie.', 'chunk_id': 1, 'page': 15},
        {'text': 'Ingredienti per orecchiette: 400g semola rimacinata, 200ml acqua tiepida, sale.', 'chunk_id': 2, 'page': 15},
        {'text': 'Impastare la semola con acqua fino ad ottenere un impasto liscio ed elastico.', 'chunk_id': 3, 'page': 16},
        {'text': 'Formare dei cilindri di pasta e tagliare pezzetti di circa 1cm.', 'chunk_id': 4, 'page': 16},
        {'text': 'Con il pollice premere ogni pezzetto trascinandolo sul tagliere per creare la forma concava.', 'chunk_id': 5, 'page': 16},
        {'text': 'Le orecchiette si abbinano tradizionalmente con cime di rapa o sugo di pomodoro.', 'chunk_id': 6, 'page': 17},
        {'text': 'La preparazione delle orecchiette richiede pratica per ottenere la forma perfetta.', 'chunk_id': 7, 'page': 17},

        # SEMI-RILEVANTI (pasta ma non orecchiette)
        {'text': 'La pasta fresca italiana si prepara con farina e uova in proporzione.', 'chunk_id': 8, 'page': 10},
        {'text': 'Gli spaghetti alla carbonara sono un piatto romano con guanciale e pecorino.', 'chunk_id': 9, 'page': 45},
        {'text': 'Le tagliatelle emiliane si preparano con farina 00 e uova fresche.', 'chunk_id': 10, 'page': 23},

        # NON RILEVANTI (altre ricette)
        {'text': 'La pizza margherita prevede pomodoro, mozzarella e basilico fresco.', 'chunk_id': 11, 'page': 67},
        {'text': 'Il tiramisù è un dolce al cucchiaio con mascarpone e caffè.', 'chunk_id': 12, 'page': 89},
        {'text': 'La parmigiana di melanzane è un piatto della tradizione meridionale.', 'chunk_id': 13, 'page': 56},
        {'text': 'Il risotto alla milanese si prepara con zafferano e brodo di carne.', 'chunk_id': 14, 'page': 34},
        {'text': 'La focaccia genovese è un pane basso condito con olio extravergine.', 'chunk_id': 15, 'page': 78},
        {'text': 'Le arancine siciliane sono sfere di riso ripiene e fritte.', 'chunk_id': 16, 'page': 92},
        {'text': 'La ribollita toscana è una zuppa di pane e verdure.', 'chunk_id': 17, 'page': 43},
        {'text': 'Il pesto genovese si prepara con basilico, pinoli, aglio e parmigiano.', 'chunk_id': 18, 'page': 29},
        {'text': 'La caponata siciliana è un contorno di melanzane in agrodolce.', 'chunk_id': 19, 'page': 61},
        {'text': 'Gli gnocchi di patate si preparano con patate lesse e farina.', 'chunk_id': 20, 'page': 38},
        {'text': 'La polenta è un piatto del nord Italia a base di farina di mais.', 'chunk_id': 21, 'page': 52},
        {'text': 'Il cacciucco livornese è una zuppa di pesce tipica toscana.', 'chunk_id': 22, 'page': 71},
        {'text': 'La porchetta umbra è un arrosto di maiale speziato.', 'chunk_id': 23, 'page': 83},
        {'text': 'Il pandoro veronese è un dolce natalizio soffice e profumato.', 'chunk_id': 24, 'page': 95},
        {'text': 'La mortadella di Bologna è un salume tipico emiliano.', 'chunk_id': 25, 'page': 18},
        {'text': 'Il limoncello è un liquore dolce a base di scorze di limone.', 'chunk_id': 26, 'page': 99},
        {'text': 'La bresaola valtellinese è carne di manzo essiccata e stagionata.', 'chunk_id': 27, 'page': 41},
        {'text': 'Il panettone milanese è un dolce lievitato con uvetta e canditi.', 'chunk_id': 28, 'page': 97},
        {'text': 'La burrata pugliese è un formaggio fresco con cuore cremoso.', 'chunk_id': 29, 'page': 32},
        {'text': 'Il prosecco veneto è un vino spumante prodotto in Veneto.', 'chunk_id': 30, 'page': 105},
    ]

    query = "Come si preparano le orecchiette?"

    print(f"📝 Chunks totali: {len(test_chunks)}")
    print(f"🔍 Query: \"{query}\"")
    print()
    print("Expected: Chunks 1-7 dovrebbero rankare nei primi 10 (orecchiette-specific)")
    print()

    # Run reranking
    start_time = time.time()

    try:
        reranked_chunks = rerank_chunks_onnx(
            query=query,
            chunks=test_chunks,
            top_k=10  # Top 10 come in produzione
        )

        elapsed_ms = (time.time() - start_time) * 1000

        print(f"✅ Reranking completato in {elapsed_ms:.1f}ms")
        print()

        # Display results
        print("📊 TOP 10 RISULTATI:")
        print("-" * 80)

        for i, chunk in enumerate(reranked_chunks, 1):
            score = chunk.get('rerank_score', 0)
            chunk_id = chunk.get('chunk_id', 'unknown')
            text_preview = chunk['text'][:65] + "..." if len(chunk['text']) > 65 else chunk['text']

            # Highlight se è chunk orecchiette-relevant
            is_relevant = chunk_id in [1, 2, 3, 4, 5, 6, 7]
            marker = "🎯" if is_relevant else "  "

            print(f"\n{marker} #{i} | Score: {score:6.3f} | ID: {chunk_id:2d}")
            print(f"       {text_preview}")

        print()
        print("-" * 80)
        print()

        # Validation
        print("🔬 VALIDATION:")
        print()

        # Check 1: Latency
        target_latency = 1000  # 1 second for 30 chunks is OK
        latency_ok = elapsed_ms < target_latency
        print(f"✓ Latency < {target_latency}ms: {elapsed_ms:.1f}ms {'✅ PASS' if latency_ok else '❌ FAIL'}")

        # Check 2: Orecchiette chunks in top 10
        top_10_ids = [c.get('chunk_id') for c in reranked_chunks[:10]]
        orecchiette_chunks = [1, 2, 3, 4, 5, 6, 7]
        orecchiette_in_top_10 = sum(1 for cid in orecchiette_chunks if cid in top_10_ids)

        # Expect at least 5/7 in top 10
        precision_ok = orecchiette_in_top_10 >= 5
        print(f"✓ Orecchiette chunks in top 10: {orecchiette_in_top_10}/7 {'✅ PASS' if precision_ok else '⚠️  MARGINAL' if orecchiette_in_top_10 >= 3 else '❌ FAIL'}")

        # Check 3: Top 3 sono tutti orecchiette
        top_3_ids = top_10_ids[:3]
        top_3_all_relevant = all(cid in orecchiette_chunks for cid in top_3_ids)
        print(f"✓ Top 3 tutti orecchiette: {top_3_all_relevant} {'✅ PASS' if top_3_all_relevant else '⚠️  MARGINAL'}")

        # Check 4: Score spread
        scores = [c.get('rerank_score', 0) for c in reranked_chunks]
        score_spread = max(scores) - min(scores)
        spread_ok = score_spread > 1.0
        print(f"✓ Score discrimination: {score_spread:.3f} {'✅ PASS' if spread_ok else '⚠️  MARGINAL'}")

        print()

        # Overall
        all_pass = latency_ok and precision_ok and top_3_all_relevant and spread_ok

        if all_pass:
            print("=" * 80)
            print("🎉 ALL CHECKS PASSED - Production Ready!")
            print("=" * 80)
            print()
            print("📈 Performance Summary:")
            print(f"   • Chunks processati: 30 (realistico)")
            print(f"   • Latency: {elapsed_ms:.1f}ms")
            print(f"   • Precision: {orecchiette_in_top_10}/7 relevant in top 10")
            print(f"   • Quality: Top 3 tutti corretti" if top_3_all_relevant else f"   • Quality: Top 3 parzialmente corretti")
            print()
            print("💰 vs Modal GPU:")
            print(f"   • Cost: $0 vs $30-50/month")
            print(f"   • Latency: {elapsed_ms:.0f}ms vs 15-25s (cold start)")
            print()
            return True
        else:
            print("=" * 80)
            print("⚠️  SOME CHECKS FAILED - Review above")
            print("=" * 80)
            print()
            return False

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"❌ Test failed after {elapsed_ms:.1f}ms")
        print(f"   Error: {e}")

        import traceback
        print()
        print("🔍 Full traceback:")
        print(traceback.format_exc())

        return False


if __name__ == "__main__":
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "REALISTIC PRODUCTION TEST - 30 Chunks + Orecchiette Query".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    success = test_realistic_scenario()

    print()
    if success:
        print("✅ ONNX Reranker validated for production deployment!")
        sys.exit(0)
    else:
        print("⚠️  Review test results before deploying")
        sys.exit(1)
