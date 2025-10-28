"""
Query Engine Integration Module
================================
Provides drop-in integration of the adaptive system with existing query_engine.py
"""

import logging
from typing import Dict, List, Optional, Any, Union
import os

from core.adaptive_query_engine import AdaptiveQueryEngine, create_adaptive_engine
from core.adaptive_retrieval import AdaptiveRetriever
from core.query_classifier import AdaptiveQueryProcessor
from core.llm_client import LLMClient

logger = logging.getLogger(__name__)


class IntegratedQueryEngine:
    """
    Wrapper class that integrates adaptive capabilities into existing query engine.
    Can be used as a drop-in replacement for the current query engine.
    """

    def __init__(self, existing_engine=None, enable_adaptive: bool = True):
        """
        Initialize integrated query engine.

        Args:
            existing_engine: Existing query engine instance (optional)
            enable_adaptive: Whether to enable adaptive features
        """
        self.existing_engine = existing_engine
        self.enable_adaptive = enable_adaptive
        self.adaptive_engine = None

        if enable_adaptive:
            self._initialize_adaptive_components()

    def _initialize_adaptive_components(self):
        """Initialize adaptive components if vector store is available"""
        if self.existing_engine and hasattr(self.existing_engine, 'vector_store'):
            try:
                # Extract components from existing engine
                vector_store = getattr(self.existing_engine, 'vector_store', None)
                bm25_index = getattr(self.existing_engine, 'bm25_index', None)
                llm_client = getattr(self.existing_engine, 'llm_client', None)
                embedding_model = getattr(self.existing_engine, 'embedding_model', None)

                if vector_store:
                    self.adaptive_engine = create_adaptive_engine(
                        vector_store=vector_store,
                        bm25_index=bm25_index,
                        llm_client=llm_client,
                        embedding_model=embedding_model
                    )
                    logger.info("Adaptive query engine initialized successfully")
                else:
                    logger.warning("Vector store not found, adaptive features disabled")
                    self.enable_adaptive = False

            except Exception as e:
                logger.error(f"Failed to initialize adaptive components: {str(e)}")
                self.enable_adaptive = False

    def query(
        self,
        query_text: str,
        doc_id: Optional[str] = None,
        use_adaptive: Optional[bool] = None,
        **kwargs
    ) -> Union[str, Dict[str, Any]]:
        """
        Process a query with optional adaptive enhancement.

        Args:
            query_text: The user query
            doc_id: Optional document ID to restrict search
            use_adaptive: Override for adaptive processing
            **kwargs: Additional parameters

        Returns:
            Query response (string or dict depending on configuration)
        """
        # Determine whether to use adaptive processing
        use_adaptive = use_adaptive if use_adaptive is not None else self.enable_adaptive

        if use_adaptive and self.adaptive_engine:
            return self._adaptive_query(query_text, doc_id, **kwargs)
        elif self.existing_engine:
            return self._legacy_query(query_text, doc_id, **kwargs)
        else:
            raise ValueError("No query engine available")

    def _adaptive_query(self, query_text: str, doc_id: Optional[str], **kwargs) -> Dict[str, Any]:
        """Process query using adaptive engine"""
        try:
            # Use adaptive engine
            result = self.adaptive_engine.query(
                query=query_text,
                include_conversation_context=kwargs.get('include_context', True),
                override_config=kwargs.get('override_config', None)
            )

            # Format response based on expected output
            if kwargs.get('return_full_result', False):
                return {
                    'answer': result.llm_response,
                    'sources': result.retrieved_chunks,
                    'metadata': result.metadata,
                    'classification': {
                        'intent': result.classification.intent.value,
                        'specificity': result.classification.specificity.value,
                        'response_type': result.classification.response_type.value,
                        'confidence': result.classification.confidence
                    },
                    'retrieval_strategy': result.retrieval_strategy,
                    'retrieval_quality': result.metadata.get('retrieval_quality', 0)
                }
            else:
                # Simple string response for backward compatibility
                return result.llm_response

        except Exception as e:
            logger.error(f"Adaptive query failed, falling back: {str(e)}")
            if self.existing_engine:
                return self._legacy_query(query_text, doc_id, **kwargs)
            else:
                raise

    def _legacy_query(self, query_text: str, doc_id: Optional[str], **kwargs) -> Any:
        """Process query using existing engine"""
        if hasattr(self.existing_engine, 'query'):
            return self.existing_engine.query(query_text, doc_id, **kwargs)
        else:
            raise NotImplementedError("Existing engine does not implement query method")

    def clear_history(self):
        """Clear conversation history"""
        if self.adaptive_engine:
            self.adaptive_engine.clear_conversation_history()
        if self.existing_engine and hasattr(self.existing_engine, 'clear_history'):
            self.existing_engine.clear_history()

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        metrics = {}

        if self.adaptive_engine:
            metrics['adaptive'] = self.adaptive_engine.get_metrics()

        if self.existing_engine and hasattr(self.existing_engine, 'get_metrics'):
            metrics['legacy'] = self.existing_engine.get_metrics()

        return metrics


def upgrade_existing_engine(engine_instance, **config) -> IntegratedQueryEngine:
    """
    Upgrade an existing query engine with adaptive capabilities.

    Args:
        engine_instance: Existing query engine instance
        **config: Configuration options

    Returns:
        IntegratedQueryEngine with adaptive features

    Example:
        ```python
        from core.query_engine import QueryEngine
        from core.query_engine_integration import upgrade_existing_engine

        # Your existing engine
        old_engine = QueryEngine(...)

        # Upgrade to adaptive
        new_engine = upgrade_existing_engine(old_engine)

        # Use the same interface
        result = new_engine.query("Come si prepara il risotto?")
        ```
    """
    return IntegratedQueryEngine(
        existing_engine=engine_instance,
        enable_adaptive=config.get('enable_adaptive', True)
    )


def create_standalone_adaptive_engine(**config) -> AdaptiveQueryEngine:
    """
    Create a standalone adaptive query engine.

    Args:
        **config: Configuration including vector_store, bm25_index, etc.

    Returns:
        Configured AdaptiveQueryEngine

    Example:
        ```python
        from core.query_engine_integration import create_standalone_adaptive_engine

        engine = create_standalone_adaptive_engine(
            vector_store=my_vector_store,
            bm25_index=my_bm25_index,
            llm_client=my_llm_client
        )

        result = engine.query("Quali ricette ci sono?")
        ```
    """
    return create_adaptive_engine(**config)


# Monkey-patch helper for existing code
def patch_query_engine_module():
    """
    Monkey-patch the existing query_engine module to use adaptive features.
    This allows existing code to benefit from adaptive features without modification.

    Usage:
        ```python
        from core.query_engine_integration import patch_query_engine_module
        patch_query_engine_module()

        # Now all existing QueryEngine instances will have adaptive features
        from core.query_engine import QueryEngine
        engine = QueryEngine(...)  # This will be adaptive-enhanced
        ```
    """
    try:
        import core.query_engine as qe

        # Store original class
        OriginalQueryEngine = qe.QueryEngine

        # Create enhanced class
        class AdaptiveEnhancedQueryEngine(OriginalQueryEngine):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Wrap with adaptive capabilities
                self._integrated = IntegratedQueryEngine(
                    existing_engine=self,
                    enable_adaptive=kwargs.get('enable_adaptive', True)
                )

            def query(self, *args, **kwargs):
                # Use integrated query with adaptive features
                return self._integrated.query(*args, **kwargs)

            def get_metrics(self):
                return self._integrated.get_metrics()

        # Replace in module
        qe.QueryEngine = AdaptiveEnhancedQueryEngine
        logger.info("Query engine module patched with adaptive capabilities")

    except Exception as e:
        logger.error(f"Failed to patch query engine module: {str(e)}")


# Configuration presets for common use cases
ADAPTIVE_PRESETS = {
    'high_precision': {
        'enable_adaptive': True,
        'override_config': {
            'initial_k': 5,
            'quality_threshold': 0.7,
            'fallback_multiplier': 2
        }
    },
    'high_recall': {
        'enable_adaptive': True,
        'override_config': {
            'initial_k': 20,
            'quality_threshold': 0.4,
            'fallback_multiplier': 1.5
        }
    },
    'balanced': {
        'enable_adaptive': True,
        'override_config': {
            'initial_k': 10,
            'quality_threshold': 0.5,
            'fallback_multiplier': 2
        }
    },
    'fast': {
        'enable_adaptive': True,
        'override_config': {
            'initial_k': 3,
            'quality_threshold': 0.6,
            'fallback_multiplier': 1,
            'max_k': 20
        }
    }
}


def get_preset_config(preset_name: str) -> Dict[str, Any]:
    """
    Get configuration preset for common use cases.

    Args:
        preset_name: One of 'high_precision', 'high_recall', 'balanced', 'fast'

    Returns:
        Configuration dictionary

    Example:
        ```python
        config = get_preset_config('high_precision')
        engine = IntegratedQueryEngine(**config)
        ```
    """
    if preset_name not in ADAPTIVE_PRESETS:
        raise ValueError(f"Unknown preset: {preset_name}. "
                        f"Available: {list(ADAPTIVE_PRESETS.keys())}")

    return ADAPTIVE_PRESETS[preset_name].copy()