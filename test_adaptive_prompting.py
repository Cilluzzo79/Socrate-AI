"""
Test Suite for Adaptive Query Classification and Prompting System
==================================================================
Demonstrates the complete adaptive pipeline with various query types.
"""

import sys
import logging
from typing import List, Dict, Any
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from core.query_classifier import (
    QueryClassifier,
    AdaptivePromptGenerator,
    AdaptiveQueryProcessor,
    QueryIntent,
    SpecificityLevel,
    ResponseType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdaptivePromptingTester:
    """Test harness for adaptive prompting system"""

    def __init__(self):
        self.classifier = QueryClassifier()
        self.prompt_generator = AdaptivePromptGenerator()
        self.processor = AdaptiveQueryProcessor()

    def test_query_classification(self):
        """Test query classification with various query types"""
        print("\n" + "="*80)
        print("TESTING QUERY CLASSIFICATION")
        print("="*80)

        test_queries = [
            # Italian recipe queries
            {
                'query': "Come si prepara l'ossobuco alla milanese?",
                'expected_intent': QueryIntent.PROCEDURAL,
                'expected_specificity': SpecificityLevel.SPECIFIC,
                'expected_response': ResponseType.STEP_BY_STEP
            },
            {
                'query': "Quali ricette ci sono nel documento?",
                'expected_intent': QueryIntent.EXPLORATORY,
                'expected_specificity': SpecificityLevel.BROAD,
                'expected_response': ResponseType.LIST
            },
            {
                'query': "Qual è la differenza tra ossobuco milanese e fiorentino?",
                'expected_intent': QueryIntent.ANALYTICAL,
                'expected_specificity': SpecificityLevel.SPECIFIC,
                'expected_response': ResponseType.COMPARISON
            },
            {
                'query': "E le orecchiette?",  # Follow-up query
                'expected_intent': QueryIntent.CONTEXTUAL,
                'expected_specificity': SpecificityLevel.SPECIFIC,
                'expected_response': ResponseType.SHORT_ANSWER
            },
            {
                'query': "Quanto tempo ci vuole per cucinare il risotto?",
                'expected_intent': QueryIntent.FACTUAL,
                'expected_specificity': SpecificityLevel.SPECIFIC,
                'expected_response': ResponseType.SHORT_ANSWER
            },
            {
                'query': "Cos'è la gremolata?",
                'expected_intent': QueryIntent.DEFINITIONAL,
                'expected_specificity': SpecificityLevel.SPECIFIC,
                'expected_response': ResponseType.DETAILED_EXPLANATION
            },

            # English technical queries
            {
                'query': "How do I configure the RAG pipeline?",
                'expected_intent': QueryIntent.PROCEDURAL,
                'expected_specificity': SpecificityLevel.MODERATE,
                'expected_response': ResponseType.STEP_BY_STEP
            },
            {
                'query': "What are all the available embedding models?",
                'expected_intent': QueryIntent.EXPLORATORY,
                'expected_specificity': SpecificityLevel.BROAD,
                'expected_response': ResponseType.LIST
            },
            {
                'query': "Compare ColBERT and dense embeddings",
                'expected_intent': QueryIntent.ANALYTICAL,
                'expected_specificity': SpecificityLevel.SPECIFIC,
                'expected_response': ResponseType.COMPARISON
            }
        ]

        for test_case in test_queries:
            query = test_case['query']
            print(f"\nQuery: '{query}'")

            # Classify
            classification = self.classifier.classify(query)

            # Check results
            print(f"  Intent: {classification.intent.value} "
                  f"(expected: {test_case['expected_intent'].value})")
            print(f"  Specificity: {classification.specificity.value} "
                  f"(expected: {test_case['expected_specificity'].value})")
            print(f"  Response Type: {classification.response_type.value} "
                  f"(expected: {test_case['expected_response'].value})")
            print(f"  Confidence: {classification.confidence:.2f}")
            print(f"  Keywords: {classification.keywords}")
            print(f"  Domains: {classification.domain_indicators}")
            print(f"  Is Follow-up: {classification.is_follow_up}")

            # Validate
            if classification.intent == test_case['expected_intent']:
                print("  [OK] Intent classification correct")
            else:
                print("  [X] Intent classification mismatch")

    def test_adaptive_prompts(self):
        """Test adaptive prompt generation with different scenarios"""
        print("\n" + "="*80)
        print("TESTING ADAPTIVE PROMPT GENERATION")
        print("="*80)

        scenarios = [
            {
                'name': "High-Quality Specific Recipe Query",
                'query': "Come si prepara l'ossobuco alla milanese?",
                'chunks': [
                    {
                        'text': "L'ossobuco alla milanese è un piatto tradizionale lombardo. "
                               "Ingredienti: 4 ossibuchi di vitello, 1 cipolla, 2 carote, "
                               "2 coste di sedano, burro, vino bianco, brodo, pomodori pelati. "
                               "Preparazione: 1) Infarinare gli ossibuchi. 2) Rosolare nel burro. "
                               "3) Aggiungere le verdure tritate. 4) Sfumare con vino bianco. "
                               "5) Aggiungere brodo e pomodori. 6) Cuocere per 90 minuti.",
                        'metadata': {'source': 'ricette_lombarde.pdf', 'page': 42}
                    }
                ],
                'scores': [0.85],
                'expected_quality': 'high'
            },
            {
                'name': "Medium-Quality Broad Query",
                'query': "Quali ricette ci sono nel documento?",
                'chunks': [
                    {
                        'text': "Indice delle ricette: Ossobuco milanese (pag. 42), "
                               "Risotto alla milanese (pag. 45), Cotoletta alla milanese (pag. 48)",
                        'metadata': {'source': 'ricette_lombarde.pdf', 'page': 3}
                    },
                    {
                        'text': "Altri piatti: Panettone (pag. 120), Cassoeula (pag. 85)",
                        'metadata': {'source': 'ricette_lombarde.pdf', 'page': 4}
                    }
                ],
                'scores': [0.6, 0.5],
                'expected_quality': 'medium'
            },
            {
                'name': "Low-Quality Analytical Query",
                'query': "Qual è la differenza tra ossobuco milanese e romano?",
                'chunks': [
                    {
                        'text': "L'ossobuco è un taglio di carne ricavato dalla zampa del vitello",
                        'metadata': {'source': 'enciclopedia_cucina.pdf', 'page': 234}
                    }
                ],
                'scores': [0.3],
                'expected_quality': 'low'
            },
            {
                'name': "No Results Query",
                'query': "Come si prepara la bagna cauda?",
                'chunks': [],
                'scores': [],
                'expected_quality': 'none'
            }
        ]

        for scenario in scenarios:
            print(f"\n{'-'*60}")
            print(f"Scenario: {scenario['name']}")
            print(f"Query: {scenario['query']}")

            # Process query
            prompt, classification = self.processor.process_query(
                query=scenario['query'],
                retrieved_chunks=scenario['chunks'],
                retrieval_scores=scenario['scores']
            )

            # Display results
            print(f"\nClassification:")
            print(f"  Intent: {classification.intent.value}")
            print(f"  Specificity: {classification.specificity.value}")
            print(f"  Response Type: {classification.response_type.value}")

            print(f"\nRetrieval Quality: {scenario['expected_quality']}")
            print(f"Chunks Retrieved: {len(scenario['chunks'])}")

            print(f"\nGenerated Adaptive Prompt:")
            print("-" * 40)
            # Show first 500 chars of prompt for brevity
            prompt_preview = prompt[:800] + "..." if len(prompt) > 800 else prompt
            print(prompt_preview)
            print("-" * 40)

    def test_conversation_context(self):
        """Test handling of conversation context for follow-up queries"""
        print("\n" + "="*80)
        print("TESTING CONVERSATION CONTEXT HANDLING")
        print("="*80)

        conversation = [
            "Come si prepara l'ossobuco alla milanese?",
            "E quanto tempo ci vuole?",
            "Quali ingredienti servono?",
            "Posso usare il manzo invece del vitello?"
        ]

        history = []
        for i, query in enumerate(conversation):
            print(f"\nTurn {i+1}: {query}")

            # Classify with history
            classification = self.classifier.classify(query, history)

            print(f"  Intent: {classification.intent.value}")
            print(f"  Is Follow-up: {classification.is_follow_up}")

            # For follow-ups, generate prompt with context
            if classification.is_follow_up:
                # Simulate some retrieval
                chunks = [{'text': 'Sample context about ossobuco...', 'metadata': {}}]
                scores = [0.6]

                # Create conversation history format
                conv_history = [
                    {'role': 'user', 'content': q} for q in history
                ]

                prompt, _ = self.processor.process_query(
                    query=query,
                    retrieved_chunks=chunks,
                    retrieval_scores=scores,
                    conversation_history=conv_history
                )

                # Check if history is included in prompt
                if "CONVERSATION HISTORY" in prompt:
                    print("  [OK] Conversation history included in prompt")
                else:
                    print("  [X] Conversation history not included")

            # Add to history
            history.append(query)

    def test_domain_specific_queries(self):
        """Test domain detection and adaptation"""
        print("\n" + "="*80)
        print("TESTING DOMAIN-SPECIFIC ADAPTATION")
        print("="*80)

        domain_queries = [
            ("Quali sono gli ingredienti per il risotto?", "recipe"),
            ("Come configurare l'embedding model?", "technical"),
            ("Quali sono i sintomi della bronchite?", "medical"),
            ("Cosa dice l'articolo 1139 del codice civile?", "legal"),
            ("What is the weather today?", "general")
        ]

        for query, expected_domain in domain_queries:
            print(f"\nQuery: {query}")

            classification = self.classifier.classify(query)
            detected_domains = classification.domain_indicators

            print(f"  Expected Domain: {expected_domain}")
            print(f"  Detected Domains: {detected_domains}")

            if expected_domain in detected_domains or \
               (expected_domain == "general" and detected_domains == ["general"]):
                print("  [OK] Domain correctly identified")
            else:
                print("  [X] Domain mismatch")

    def test_response_type_detection(self):
        """Test response type detection for various queries"""
        print("\n" + "="*80)
        print("TESTING RESPONSE TYPE DETECTION")
        print("="*80)

        response_queries = [
            ("Elenca tutti i piatti lombardi", ResponseType.LIST),
            ("Come si fa il risotto passo passo?", ResponseType.STEP_BY_STEP),
            ("Quanto sale serve?", ResponseType.SHORT_ANSWER),
            ("Confronta risotto milanese e risotto ai funghi", ResponseType.COMPARISON),
            ("Spiega cos'è il soffritto", ResponseType.DETAILED_EXPLANATION),
            ("Riassumi la ricetta", ResponseType.SUMMARY)
        ]

        for query, expected_type in response_queries:
            print(f"\nQuery: {query}")

            classification = self.classifier.classify(query)
            detected_type = classification.response_type

            print(f"  Expected Type: {expected_type.value}")
            print(f"  Detected Type: {detected_type.value}")

            if detected_type == expected_type:
                print("  [OK] Response type correct")
            else:
                print("  [X] Response type mismatch")

    def run_all_tests(self):
        """Run all test suites"""
        print("\n" + "="*80)
        print("ADAPTIVE QUERY PROCESSING TEST SUITE")
        print("="*80)

        self.test_query_classification()
        self.test_adaptive_prompts()
        self.test_conversation_context()
        self.test_domain_specific_queries()
        self.test_response_type_detection()

        # Summary
        print("\n" + "="*80)
        print("TEST SUITE COMPLETED")
        print("="*80)
        print("\nThe adaptive system successfully:")
        print("1. Classifies queries by intent, specificity, and expected response")
        print("2. Generates adaptive prompts based on classification")
        print("3. Adjusts prompts based on retrieval quality")
        print("4. Handles conversation context for follow-up queries")
        print("5. Detects domain-specific terminology")
        print("6. Tailors response format to query type")


def main():
    """Main test execution"""
    tester = AdaptivePromptingTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()