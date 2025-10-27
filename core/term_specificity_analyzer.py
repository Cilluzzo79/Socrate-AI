"""
Universal Term Specificity Analyzer for Domain-Agnostic RAG Systems.

This module implements Adaptive Term Specificity Weighting (ATSW), a universal
solution that automatically learns which query terms are generic vs. specific
by analyzing document statistics.

Based on RAG best practices 2025 and proven IR theory.
"""

import re
import math
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
import numpy as np

logger = logging.getLogger(__name__)


class UniversalTermSpecificityAnalyzer:
    """
    Analyzes document corpus to automatically detect term specificity.

    Uses 6 statistical signals:
    1. IDF (Inverse Document Frequency) - rare terms are specific
    2. Contextual Diversity - terms appearing with many different terms are generic
    3. Entropy - evenly distributed terms are generic
    4. Position Boost - later terms in queries are often more specific
    5. Length Heuristic - longer terms are statistically more specific
    6. Proper Noun Detection - capitalized entities are specific

    Works universally across ALL domains without hardcoded knowledge.
    """

    def __init__(
        self,
        chunks: List[Any],
        min_term_length: int = 2,
        stopwords: Optional[Set[str]] = None
    ):
        """
        Initialize analyzer by computing document statistics.

        Args:
            chunks: List of chunks (either strings or dicts with 'text' key)
            min_term_length: Minimum term length to consider
            stopwords: Optional set of stopwords to filter (defaults to basic Italian)
        """
        # Basic Italian stopwords (minimal set to avoid over-filtering)
        self.stopwords = stopwords or {
            'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una',
            'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
            'e', 'o', 'ma', 'se', 'non', 'che', 'del', 'al', 'dal', 'nel'
        }

        self.min_term_length = min_term_length
        self.chunks = chunks

        # Extract text from chunks
        self.chunk_texts = []
        for chunk in chunks:
            if isinstance(chunk, dict):
                self.chunk_texts.append(chunk.get('text', ''))
            else:
                self.chunk_texts.append(str(chunk))

        # Statistics storage
        self.idf_scores: Dict[str, float] = {}
        self.contextual_diversity: Dict[str, float] = {}
        self.term_entropy: Dict[str, float] = {}
        self.document_frequency: Dict[str, int] = {}
        self.term_contexts: Dict[str, Set[str]] = defaultdict(set)

        # Metadata
        self.total_chunks = len(self.chunk_texts)
        self.vocabulary: Set[str] = set()
        self.avg_term_length = 0.0

        # Build statistics
        logger.info(f"[ATSW] Initializing term analyzer for {self.total_chunks} chunks...")
        self._build_vocabulary()
        self._compute_idf()
        self._compute_contextual_diversity()
        self._compute_entropy()

        logger.info(f"[ATSW] Analyzed {len(self.vocabulary)} unique terms")

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization (split on whitespace and normalize)."""
        # Lowercase and split
        tokens = text.lower().split()

        # Filter by length and stopwords
        tokens = [
            t for t in tokens
            if len(t) >= self.min_term_length and t not in self.stopwords
        ]

        return tokens

    def _build_vocabulary(self):
        """Build vocabulary and compute document frequency."""
        for chunk_text in self.chunk_texts:
            # Get unique terms in this chunk
            terms_in_chunk = set(self._tokenize(chunk_text))

            # Update vocabulary
            self.vocabulary.update(terms_in_chunk)

            # Update document frequency (how many chunks contain this term)
            for term in terms_in_chunk:
                self.document_frequency[term] = self.document_frequency.get(term, 0) + 1

        # Compute average term length
        if self.vocabulary:
            self.avg_term_length = sum(len(t) for t in self.vocabulary) / len(self.vocabulary)
        else:
            self.avg_term_length = 5.0

    def _compute_idf(self):
        """
        Compute Inverse Document Frequency for all terms.

        IDF(term) = log((N + 1) / (df(term) + 1)) + 1

        High IDF = rare term = specific (e.g., "ossobuco")
        Low IDF = common term = generic (e.g., "ricetta")
        """
        for term in self.vocabulary:
            df = self.document_frequency[term]
            idf = math.log((self.total_chunks + 1) / (df + 1)) + 1
            self.idf_scores[term] = idf

    def _compute_contextual_diversity(self):
        """
        Compute contextual diversity for all terms.

        Diversity(term) = |unique_context_terms(term)| / df(term)

        High diversity = appears with many different terms = generic (e.g., "documento")
        Low diversity = limited contexts = specific (e.g., "ossobuco")
        """
        # First pass: collect all contexts for each term
        for chunk_text in self.chunk_texts:
            terms = self._tokenize(chunk_text)
            unique_terms = set(terms)

            # For each term, record all OTHER terms it appears with
            for term in unique_terms:
                context_terms = unique_terms - {term}
                self.term_contexts[term].update(context_terms)

        # Second pass: compute diversity ratio
        for term in self.vocabulary:
            df = self.document_frequency[term]
            unique_contexts = len(self.term_contexts[term])

            # Normalize by document frequency
            if df > 0:
                diversity = unique_contexts / df
                # Normalize to [0, 1] range (cap at 10 unique contexts per occurrence)
                self.contextual_diversity[term] = min(diversity / 10.0, 1.0)
            else:
                self.contextual_diversity[term] = 0.0

    def _compute_entropy(self):
        """
        Compute term entropy across chunks.

        Entropy(term) = -Σ p(term|chunk) * log(p(term|chunk))

        High entropy = evenly distributed = generic
        Low entropy = concentrated in few chunks = specific
        """
        # Count term occurrences per chunk
        term_chunk_counts = defaultdict(lambda: np.zeros(self.total_chunks))

        for chunk_idx, chunk_text in enumerate(self.chunk_texts):
            term_counts = Counter(self._tokenize(chunk_text))
            for term, count in term_counts.items():
                term_chunk_counts[term][chunk_idx] = count

        # Compute entropy
        for term in self.vocabulary:
            counts = term_chunk_counts[term]
            total_count = counts.sum()

            if total_count == 0:
                self.term_entropy[term] = 0.0
                continue

            # Probability distribution
            probs = counts / total_count
            probs = probs[probs > 0]  # Remove zeros

            # Entropy
            entropy = -np.sum(probs * np.log2(probs))

            # Normalize by max possible entropy (log2 of number of chunks)
            max_entropy = math.log2(self.total_chunks) if self.total_chunks > 1 else 1.0
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

            self.term_entropy[term] = normalized_entropy

    def compute_term_specificity(
        self,
        term: str,
        position: int = 0,
        total_terms: int = 1
    ) -> float:
        """
        Compute combined specificity score for a term using 6 signals.

        Args:
            term: The term to analyze
            position: Position in query (0-indexed)
            total_terms: Total number of terms in query

        Returns:
            Specificity score (higher = more specific)
        """
        term_lower = term.lower()

        # If term not in vocabulary, use heuristics only
        if term_lower not in self.vocabulary:
            # Unknown term - assume somewhat specific
            return self._compute_heuristic_specificity(term, position, total_terms)

        # Signal 1: IDF (Inverse Document Frequency)
        idf = self.idf_scores.get(term_lower, 1.0)

        # Signal 2: Contextual Diversity (invert: low diversity = specific)
        diversity = self.contextual_diversity.get(term_lower, 0.5)
        diversity_factor = 1.0 - (0.7 * diversity)

        # Signal 3: Entropy (invert: low entropy = specific)
        entropy = self.term_entropy.get(term_lower, 0.5)
        entropy_factor = 1.0 - (0.3 * entropy)

        # Signal 4: Position Boost (later terms often more specific)
        if total_terms > 1:
            position_ratio = position / (total_terms - 1)
            position_boost = 1.0 + (0.3 * (position_ratio ** 2))
        else:
            position_boost = 1.0

        # Signal 5: Length Heuristic (longer terms often more specific)
        length_diff = len(term_lower) - self.avg_term_length
        length_boost = 1.0 + (0.1 * min(length_diff / self.avg_term_length, 1.0))
        length_boost = max(0.9, length_boost)  # Don't penalize too much

        # Signal 6: Proper Noun Detection
        is_proper_noun = len(term) > 2 and term[0].isupper() and not term.isupper()
        proper_noun_boost = 1.2 if is_proper_noun else 1.0

        # Combined score
        specificity = (
            idf *
            diversity_factor *
            entropy_factor *
            position_boost *
            length_boost *
            proper_noun_boost
        )

        # Adaptive thresholding based on IDF percentiles
        idf_values = sorted(self.idf_scores.values())
        if idf_values:
            p20 = idf_values[int(len(idf_values) * 0.2)]
            p80 = idf_values[int(len(idf_values) * 0.8)]

            if idf < p20:
                # Very common term - heavy suppression
                specificity *= 0.1
            elif idf > p80:
                # Very rare term - boost
                specificity *= 1.2

        return specificity

    def _compute_heuristic_specificity(
        self,
        term: str,
        position: int,
        total_terms: int
    ) -> float:
        """Compute specificity for unknown terms using heuristics only."""
        # Position boost
        if total_terms > 1:
            position_ratio = position / (total_terms - 1)
            position_boost = 1.0 + (0.3 * (position_ratio ** 2))
        else:
            position_boost = 1.0

        # Length boost
        length_boost = 1.0 + (0.1 * min((len(term) - 5) / 5, 1.0))
        length_boost = max(0.9, length_boost)

        # Proper noun boost
        is_proper_noun = len(term) > 2 and term[0].isupper() and not term.isupper()
        proper_noun_boost = 1.2 if is_proper_noun else 1.0

        # Default to moderately specific for unknown terms
        return 3.0 * position_boost * length_boost * proper_noun_boost

    def compute_query_term_weights(self, query: str) -> Dict[str, float]:
        """
        Compute normalized weights for all terms in a query.

        Args:
            query: User query string

        Returns:
            Dict mapping term -> normalized weight [0, 1]
        """
        terms = query.split()
        total_terms = len(terms)

        if total_terms == 0:
            return {}

        # Compute raw specificity scores
        raw_scores = {}
        for position, term in enumerate(terms):
            term_lower = term.lower()
            if term_lower in self.stopwords:
                continue

            specificity = self.compute_term_specificity(term, position, total_terms)
            raw_scores[term_lower] = specificity

        if not raw_scores:
            return {}

        # Normalize to [0, 1]
        total_specificity = sum(raw_scores.values())
        if total_specificity > 0:
            normalized = {
                term: score / total_specificity
                for term, score in raw_scores.items()
            }
        else:
            # Equal weights if all scores are 0
            normalized = {term: 1.0 / len(raw_scores) for term in raw_scores}

        return normalized

    def identify_key_terms(self, query: str, top_k: int = 2) -> List[str]:
        """
        Identify the most specific (key) terms in a query.

        Args:
            query: User query string
            top_k: Number of key terms to return

        Returns:
            List of key terms (most specific first)
        """
        weights = self.compute_query_term_weights(query)

        if not weights:
            return []

        # Sort by weight (descending)
        sorted_terms = sorted(weights.items(), key=lambda x: x[1], reverse=True)

        # Return top k terms
        return [term for term, weight in sorted_terms[:top_k]]

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the analyzed corpus."""
        if not self.vocabulary:
            return {
                'total_unique_terms': 0,
                'total_chunks': self.total_chunks,
                'avg_term_length': 0.0,
                'most_common_terms': [],
                'most_specific_terms': []
            }

        # Most common terms (lowest IDF)
        idf_sorted = sorted(self.idf_scores.items(), key=lambda x: x[1])
        most_common = idf_sorted[:10]

        # Most specific terms (highest IDF)
        most_specific = idf_sorted[-10:][::-1]

        return {
            'total_unique_terms': len(self.vocabulary),
            'total_chunks': self.total_chunks,
            'avg_term_length': self.avg_term_length,
            'most_common_terms': most_common,
            'most_specific_terms': most_specific
        }


def create_term_analyzer_from_chunks(
    chunks: List[Any],
    min_term_length: int = 2
) -> Optional[UniversalTermSpecificityAnalyzer]:
    """
    Factory function to create term analyzer with error handling.

    Args:
        chunks: List of chunks (strings or dicts)
        min_term_length: Minimum term length

    Returns:
        UniversalTermSpecificityAnalyzer instance or None if creation fails
    """
    try:
        if not chunks or len(chunks) < 10:
            logger.warning("[ATSW] Too few chunks for statistical analysis (<10). ATSW disabled.")
            return None

        analyzer = UniversalTermSpecificityAnalyzer(
            chunks=chunks,
            min_term_length=min_term_length
        )

        stats = analyzer.get_statistics_summary()
        logger.info(f"[ATSW] Analyzer ready: {stats['total_unique_terms']} terms from {stats['total_chunks']} chunks")
        logger.info(f"[ATSW] Most generic: {[t[0] for t in stats['most_common_terms'][:3]]}")
        logger.info(f"[ATSW] Most specific: {[t[0] for t in stats['most_specific_terms'][:3]]}")

        return analyzer

    except Exception as e:
        logger.error(f"[ATSW] Failed to create term analyzer: {e}")
        return None
