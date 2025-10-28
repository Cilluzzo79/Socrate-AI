"""
Adaptive Query Engine Integration
==================================
Integrates the adaptive retrieval system with adaptive prompt generation
for end-to-end query processing optimization.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from core.query_classifier import (
    AdaptiveQueryProcessor,
    QueryClassification,
    QueryIntent,
    SpecificityLevel
)
from core.adaptive_retrieval import AdaptiveRetriever
from core.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveQueryResult:
    """Complete result from adaptive query processing"""
    query: str
    classification: QueryClassification
    retrieved_chunks: List[Dict[str, Any]]
    retrieval_scores: List[float]
    retrieval_strategy: str
    adaptive_prompt: str
    llm_response: str
    metadata: Dict[str, Any]


class AdaptiveQueryEngine:
    """
    Complete adaptive query engine that combines:
    1. Query classification
    2. Adaptive retrieval
    3. Adaptive prompt generation
    4. LLM response generation
    """

    def __init__(
        self,
        vector_store,
        bm25_index,
        llm_client: Optional[LLMClient] = None,
        embedding_model=None
    ):
        """
        Initialize the adaptive query engine.

        Args:
            vector_store: Vector store for semantic search
            bm25_index: BM25 index for keyword search
            llm_client: LLM client for response generation
            embedding_model: Embedding model for queries
        """
        # Initialize components
        self.adaptive_retriever = AdaptiveRetriever(
            vector_store=vector_store,
            bm25_index=bm25_index,
            embedding_model=embedding_model
        )

        self.query_processor = AdaptiveQueryProcessor()
        self.llm_client = llm_client or LLMClient()

        # Configuration
        self.config = self._initialize_config()

        # Conversation history (for contextual queries)
        self.conversation_history = []

    def _initialize_config(self) -> Dict[str, Any]:
        """Initialize configuration based on query types"""
        return {
            # Retrieval configuration per intent
            'retrieval_config': {
                QueryIntent.FACTUAL: {
                    'initial_k': 5,
                    'fallback_multiplier': 2,
                    'quality_threshold': 0.7
                },
                QueryIntent.PROCEDURAL: {
                    'initial_k': 10,  # Need more context for procedures
                    'fallback_multiplier': 2,
                    'quality_threshold': 0.6
                },
                QueryIntent.EXPLORATORY: {
                    'initial_k': 20,  # Cast a wide net for exploration
                    'fallback_multiplier': 1.5,
                    'quality_threshold': 0.4
                },
                QueryIntent.ANALYTICAL: {
                    'initial_k': 15,  # Need multiple perspectives
                    'fallback_multiplier': 2,
                    'quality_threshold': 0.5
                },
                QueryIntent.DEFINITIONAL: {
                    'initial_k': 5,
                    'fallback_multiplier': 3,
                    'quality_threshold': 0.6
                },
                QueryIntent.CONTEXTUAL: {
                    'initial_k': 5,
                    'fallback_multiplier': 2,
                    'quality_threshold': 0.5
                }
            },

            # LLM configuration per response type
            'llm_config': {
                'temperature': {
                    'SHORT_ANSWER': 0.1,
                    'DETAILED_EXPLANATION': 0.3,
                    'STEP_BY_STEP': 0.2,
                    'LIST': 0.1,
                    'COMPARISON': 0.3,
                    'SUMMARY': 0.2
                },
                'max_tokens': {
                    'SHORT_ANSWER': 150,
                    'DETAILED_EXPLANATION': 1000,
                    'STEP_BY_STEP': 800,
                    'LIST': 600,
                    'COMPARISON': 800,
                    'SUMMARY': 500
                }
            }
        }

    def query(
        self,
        query: str,
        include_conversation_context: bool = True,
        override_config: Optional[Dict[str, Any]] = None
    ) -> AdaptiveQueryResult:
        """
        Process a query through the complete adaptive pipeline.

        Args:
            query: User query
            include_conversation_context: Whether to include conversation history
            override_config: Optional configuration overrides

        Returns:
            AdaptiveQueryResult with complete processing information
        """
        try:
            # Step 1: Classify the query
            logger.info(f"Processing query: {query[:100]}...")

            # Get conversation history if needed
            history = self.conversation_history if include_conversation_context else None

            # Initial classification (without retrieval)
            initial_classification = self.query_processor.classifier.classify(query, history)

            # Step 2: Configure retrieval based on classification
            retrieval_config = self._get_retrieval_config(initial_classification, override_config)

            # Step 3: Perform adaptive retrieval
            retrieval_result = self.adaptive_retriever.adaptive_retrieve(
                query=query,
                initial_k=retrieval_config['initial_k'],
                quality_threshold=retrieval_config['quality_threshold'],
                fallback_multiplier=retrieval_config['fallback_multiplier'],
                max_k=100  # Maximum chunks to consider
            )

            # Step 4: Generate adaptive prompt
            adaptive_prompt, final_classification = self.query_processor.process_query(
                query=query,
                retrieved_chunks=retrieval_result['chunks'],
                retrieval_scores=retrieval_result['scores'],
                conversation_history=history
            )

            # Step 5: Generate LLM response
            llm_response = self._generate_llm_response(
                prompt=adaptive_prompt,
                classification=final_classification,
                retrieval_quality=retrieval_result['final_quality']
            )

            # Step 6: Update conversation history
            self._update_conversation_history(query, llm_response)

            # Step 7: Compile results
            result = AdaptiveQueryResult(
                query=query,
                classification=final_classification,
                retrieved_chunks=retrieval_result['chunks'],
                retrieval_scores=retrieval_result['scores'],
                retrieval_strategy=retrieval_result['strategy_used'],
                adaptive_prompt=adaptive_prompt,
                llm_response=llm_response,
                metadata={
                    'retrieval_stages': retrieval_result['stages'],
                    'retrieval_quality': retrieval_result['final_quality'],
                    'chunks_retrieved': retrieval_result['chunks_retrieved'],
                    'chunks_considered': retrieval_result['chunks_considered'],
                    'intent_confidence': final_classification.confidence,
                    'processing_time': retrieval_result.get('processing_time', 0)
                }
            )

            # Log success metrics
            logger.info(f"Query processed successfully: "
                       f"Intent={final_classification.intent.value}, "
                       f"Strategy={retrieval_result['strategy_used']}, "
                       f"Quality={retrieval_result['final_quality']:.2f}")

            return result

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    def _get_retrieval_config(
        self,
        classification: QueryClassification,
        override_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get retrieval configuration based on query classification"""
        base_config = self.config['retrieval_config'].get(
            classification.intent,
            self.config['retrieval_config'][QueryIntent.FACTUAL]  # Default
        )

        # Adjust based on specificity
        if classification.specificity == SpecificityLevel.BROAD:
            base_config = base_config.copy()
            base_config['initial_k'] = int(base_config['initial_k'] * 1.5)
            base_config['quality_threshold'] *= 0.8
        elif classification.specificity == SpecificityLevel.SPECIFIC:
            base_config = base_config.copy()
            base_config['initial_k'] = max(3, int(base_config['initial_k'] * 0.7))
            base_config['quality_threshold'] *= 1.1

        # Apply overrides if provided
        if override_config:
            base_config.update(override_config)

        return base_config

    def _generate_llm_response(
        self,
        prompt: str,
        classification: QueryClassification,
        retrieval_quality: float
    ) -> str:
        """Generate LLM response with adaptive parameters"""
        # Get LLM parameters based on response type
        response_type_str = classification.response_type.value.upper()
        temperature = self.config['llm_config']['temperature'].get(
            response_type_str, 0.3
        )
        max_tokens = self.config['llm_config']['max_tokens'].get(
            response_type_str, 500
        )

        # Adjust temperature based on retrieval quality
        if retrieval_quality < 0.4:
            # Low quality retrieval - be more conservative
            temperature *= 0.5
        elif retrieval_quality > 0.7:
            # High quality retrieval - can be slightly more creative
            temperature *= 1.2

        # Ensure temperature stays in valid range
        temperature = max(0.0, min(1.0, temperature))

        # Generate response
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=None  # Already included in adaptive prompt
            )

            # Post-process based on response type
            response = self._post_process_response(response, classification)

            return response

        except Exception as e:
            logger.error(f"LLM generation error: {str(e)}")
            # Provide a fallback response
            return self._generate_fallback_response(classification, retrieval_quality)

    def _post_process_response(self, response: str, classification: QueryClassification) -> str:
        """Post-process LLM response based on classification"""
        # Clean up common issues
        response = response.strip()

        # Format based on response type
        if classification.response_type.value == "LIST":
            # Ensure proper list formatting
            lines = response.split('\n')
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith(('•', '-', '*', '1', '2', '3')):
                    line = f"• {line}"
                formatted_lines.append(line)
            response = '\n'.join(formatted_lines)

        elif classification.response_type.value == "STEP_BY_STEP":
            # Ensure proper step numbering
            lines = response.split('\n')
            step_lines = []
            step_num = 1
            for line in lines:
                line = line.strip()
                if line and not any(line.startswith(str(i)) for i in range(1, 10)):
                    if 'step' in line.lower() or 'passaggio' in line.lower():
                        line = f"{step_num}. {line}"
                        step_num += 1
                step_lines.append(line)
            response = '\n'.join(step_lines)

        return response

    def _generate_fallback_response(
        self,
        classification: QueryClassification,
        retrieval_quality: float
    ) -> str:
        """Generate a fallback response when LLM fails"""
        if retrieval_quality < 0.3:
            return (
                "Mi dispiace, non ho trovato informazioni sufficienti nel database "
                "per rispondere alla tua domanda. Potresti riformulare la richiesta "
                "o fornire maggiori dettagli?"
            )
        else:
            return (
                "Si è verificato un errore nell'elaborazione della risposta. "
                "Per favore, riprova tra qualche istante."
            )

    def _update_conversation_history(self, query: str, response: str):
        """Update conversation history for contextual queries"""
        self.conversation_history.append({
            'role': 'user',
            'content': query
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': response
        })

        # Keep only last 5 turns (10 messages)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics"""
        metrics = self.query_processor.get_metrics_summary()
        metrics['retriever_metrics'] = self.adaptive_retriever.get_metrics()
        return metrics


def create_adaptive_engine(
    vector_store,
    bm25_index,
    llm_client: Optional[LLMClient] = None,
    embedding_model=None
) -> AdaptiveQueryEngine:
    """
    Factory function to create a configured adaptive query engine.

    Args:
        vector_store: Vector store instance
        bm25_index: BM25 index instance
        llm_client: Optional LLM client
        embedding_model: Optional embedding model

    Returns:
        Configured AdaptiveQueryEngine instance
    """
    engine = AdaptiveQueryEngine(
        vector_store=vector_store,
        bm25_index=bm25_index,
        llm_client=llm_client,
        embedding_model=embedding_model
    )

    logger.info("Adaptive query engine initialized with query classification and adaptive retrieval")

    return engine