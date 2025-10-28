"""
Query Classification and Adaptive Prompting System
==================================================
Analyzes user queries to determine intent, specificity, and expected response type,
then generates adaptive prompts for optimal LLM responses.

Based on principles from Section 5.3 (Query-Document Alignment) of the RAG Best Practices Guide.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Primary intent categories for queries"""
    FACTUAL = "factual"           # Looking for specific facts
    PROCEDURAL = "procedural"     # How-to questions
    EXPLORATORY = "exploratory"   # Browsing/discovery queries
    ANALYTICAL = "analytical"     # Comparison, analysis, reasoning
    DEFINITIONAL = "definitional" # What is X?
    CONTEXTUAL = "contextual"     # Follow-up questions


class SpecificityLevel(Enum):
    """Query specificity levels"""
    SPECIFIC = "specific"     # Narrow, focused query
    MODERATE = "moderate"     # Balanced scope
    BROAD = "broad"          # Wide-ranging query


class ResponseType(Enum):
    """Expected response formats"""
    SHORT_ANSWER = "short_answer"
    DETAILED_EXPLANATION = "detailed_explanation"
    STEP_BY_STEP = "step_by_step"
    LIST = "list"
    COMPARISON = "comparison"
    SUMMARY = "summary"


@dataclass
class QueryClassification:
    """Complete classification of a user query"""
    query: str
    intent: QueryIntent
    specificity: SpecificityLevel
    response_type: ResponseType
    domain_indicators: List[str]
    confidence: float
    keywords: List[str]
    is_follow_up: bool


class QueryClassifier:
    """
    Lightweight query classifier using pattern matching and heuristics.
    Designed for low latency without heavy NLP models.
    """

    def __init__(self):
        # Italian and English pattern mappings
        self.intent_patterns = {
            QueryIntent.PROCEDURAL: [
                r'\b(come|how|preparare|prepare|fare|make|cucinare|cook)\b',
                r'\b(passaggi|steps|procedura|procedure|metodo|method)\b',
                r'\b(ricetta|recipe|istruzioni|instructions)\b'
            ],
            QueryIntent.FACTUAL: [
                r'\b(quanto|quanti|quante|how much|how many)\b',
                r'\b(quale|quali|which|what)\s+\w+\s+(è|sono|is|are)\b',
                r'\b(ingredienti|ingredients|tempo|time|temperatura|temperature)\b'
            ],
            QueryIntent.EXPLORATORY: [
                r'\b(quali|what|che|which)\s+\w+\s+(ci sono|esistono|are there|exist)\b',
                r'\b(elenco|list|tutti|all|disponibili|available)\b',
                r'\b(mostra|show|trova|find|cerca|search)\b'
            ],
            QueryIntent.ANALYTICAL: [
                r'\b(differenza|difference|confronto|compare|versus|vs)\b',
                r'\b(meglio|better|peggio|worse|vantaggi|advantages)\b',
                r'\b(perché|why|quando|when|dove|where)\b'
            ],
            QueryIntent.DEFINITIONAL: [
                r'\b(cos\'è|cosa è|what is|che cosa|what\'s)\b',
                r'\b(definizione|definition|significa|means|chiamato|called)\b'
            ]
        }

        self.specificity_indicators = {
            'specific': [
                r'\b(specifico|specific|particolare|particular|esatto|exact)\b',
                r'\"[^\"]+\"',  # Quoted terms
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Proper nouns
                r'\b(milanese|fiorentino|romano|napoletano)\b'  # Specific variants
            ],
            'broad': [
                r'\b(tutti|all|ogni|every|qualsiasi|any)\b',
                r'\b(generale|general|vari|various|diversi|different)\b',
                r'\b(panoramica|overview|riassunto|summary)\b'
            ]
        }

        self.response_type_patterns = {
            ResponseType.STEP_BY_STEP: [
                r'\b(passaggi|steps|passo\s+passo|step\s+by\s+step)\b',
                r'\b(procedura|procedure|istruzioni|instructions)\b'
            ],
            ResponseType.LIST: [
                r'\b(elenca|list|elenco|enumera|enumerate)\b',
                r'\b(quali sono|what are|che ci sono|that exist)\b'
            ],
            ResponseType.COMPARISON: [
                r'\b(confronta|compare|differenza|difference)\b',
                r'\b(versus|vs|contro|against)\b'
            ],
            ResponseType.SHORT_ANSWER: [
                r'\b(quanto|how much|quanti|how many)\b',
                r'\b(sì o no|yes or no|vero o falso|true or false)\b'
            ]
        }

        # Domain-specific vocabulary
        self.domain_keywords = {
            'recipe': ['ricetta', 'ingredienti', 'cottura', 'preparazione', 'cucina'],
            'technical': ['configurazione', 'sistema', 'errore', 'debug', 'API'],
            'medical': ['sintomi', 'diagnosi', 'terapia', 'farmaco', 'paziente'],
            'legal': ['contratto', 'legge', 'articolo', 'comma', 'normativa']
        }

    def classify(self, query: str, conversation_history: Optional[List[str]] = None) -> QueryClassification:
        """
        Classify a query based on patterns and heuristics.

        Args:
            query: The user query to classify
            conversation_history: Previous queries in the conversation

        Returns:
            QueryClassification with all dimensions analyzed
        """
        query_lower = query.lower()

        # Extract keywords (simple tokenization)
        keywords = self._extract_keywords(query)

        # Determine if it's a follow-up query
        is_follow_up = self._is_follow_up(query, conversation_history)

        # Classify intent
        intent, intent_confidence = self._classify_intent(query_lower, is_follow_up)

        # Determine specificity
        specificity = self._determine_specificity(query_lower, keywords)

        # Determine expected response type
        response_type = self._determine_response_type(query_lower, intent)

        # Identify domain indicators
        domain_indicators = self._identify_domain(query_lower)

        return QueryClassification(
            query=query,
            intent=intent,
            specificity=specificity,
            response_type=response_type,
            domain_indicators=domain_indicators,
            confidence=intent_confidence,
            keywords=keywords,
            is_follow_up=is_follow_up
        )

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract significant keywords from query"""
        # Remove common stop words (Italian and English)
        stop_words = {'il', 'la', 'i', 'le', 'un', 'una', 'e', 'è', 'di', 'a', 'da',
                      'the', 'a', 'an', 'and', 'is', 'of', 'to', 'from', 'in', 'on'}

        # Simple tokenization
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords

    def _is_follow_up(self, query: str, history: Optional[List[str]]) -> bool:
        """Determine if query is a follow-up to previous conversation"""
        if not history:
            return False

        # Check for pronouns or references
        follow_up_patterns = [
            r'\b(questo|questa|quello|quella|it|this|that)\b',
            r'\b(stesso|stessa|same|anche|also|inoltre|moreover)\b',
            r'^(e |and |inoltre|also|anche)',  # Starting with conjunctions
            r'\?$'  # Very short questions often are follow-ups
        ]

        query_lower = query.lower()

        # Short queries are often follow-ups
        if len(query.split()) <= 3:
            return True

        # Check patterns
        for pattern in follow_up_patterns:
            if re.search(pattern, query_lower):
                return True

        return False

    def _classify_intent(self, query_lower: str, is_follow_up: bool) -> Tuple[QueryIntent, float]:
        """Classify the primary intent of the query"""
        if is_follow_up:
            return QueryIntent.CONTEXTUAL, 0.8

        intent_scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            intent_scores[intent] = score

        # Get the intent with highest score
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            if best_intent[1] > 0:
                # Confidence based on how many patterns matched
                confidence = min(best_intent[1] / 3.0, 1.0)
                return best_intent[0], confidence

        # Default to factual with low confidence
        return QueryIntent.FACTUAL, 0.3

    def _determine_specificity(self, query_lower: str, keywords: List[str]) -> SpecificityLevel:
        """Determine query specificity level"""
        specific_score = 0
        broad_score = 0

        # Check specific indicators
        for pattern in self.specificity_indicators['specific']:
            if re.search(pattern, query_lower):
                specific_score += 1

        # Check broad indicators
        for pattern in self.specificity_indicators['broad']:
            if re.search(pattern, query_lower):
                broad_score += 1

        # Consider query length and keyword count
        word_count = len(query_lower.split())
        if word_count < 5:
            specific_score += 1
        elif word_count > 15:
            broad_score += 1

        # Determine specificity
        if specific_score > broad_score:
            return SpecificityLevel.SPECIFIC
        elif broad_score > specific_score:
            return SpecificityLevel.BROAD
        else:
            return SpecificityLevel.MODERATE

    def _determine_response_type(self, query_lower: str, intent: QueryIntent) -> ResponseType:
        """Determine expected response type"""
        # Check explicit patterns
        for response_type, patterns in self.response_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return response_type

        # Infer from intent
        intent_to_response = {
            QueryIntent.PROCEDURAL: ResponseType.STEP_BY_STEP,
            QueryIntent.EXPLORATORY: ResponseType.LIST,
            QueryIntent.ANALYTICAL: ResponseType.COMPARISON,
            QueryIntent.DEFINITIONAL: ResponseType.DETAILED_EXPLANATION,
            QueryIntent.FACTUAL: ResponseType.SHORT_ANSWER,
            QueryIntent.CONTEXTUAL: ResponseType.SHORT_ANSWER
        }

        return intent_to_response.get(intent, ResponseType.DETAILED_EXPLANATION)

    def _identify_domain(self, query_lower: str) -> List[str]:
        """Identify domain indicators in the query"""
        domains = []

        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    domains.append(domain)
                    break

        return domains if domains else ['general']


class AdaptivePromptGenerator:
    """
    Generates adaptive prompts based on query classification and retrieval quality.
    Implements strategies from Section 5.2 (Context Window Optimization) of the guide.
    """

    def __init__(self):
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, str]:
        """Initialize prompt templates for different scenarios"""
        return {
            # Base instruction templates
            'base_instruction': {
                QueryIntent.FACTUAL: """You are a precise information assistant. Answer the specific question directly using only the provided context. Be concise and accurate.""",

                QueryIntent.PROCEDURAL: """You are a helpful guide. Provide clear, step-by-step instructions based on the provided context. Structure your response as:
1. Required materials/ingredients (if applicable)
2. Step-by-step procedure
3. Important tips or warnings""",

                QueryIntent.EXPLORATORY: """You are a comprehensive information organizer. List and briefly describe ALL relevant items found in the context. Use clear categorization if appropriate.""",

                QueryIntent.ANALYTICAL: """You are an analytical assistant. Compare and contrast the information provided, highlighting key differences, similarities, and insights.""",

                QueryIntent.DEFINITIONAL: """You are a clear explainer. Define and explain the concept thoroughly using the provided context. Include examples if available.""",

                QueryIntent.CONTEXTUAL: """You are a context-aware assistant continuing a conversation. Use previous context and new information to provide a relevant response."""
            },

            # Retrieval quality modifiers
            'retrieval_quality': {
                'high': "The following context contains comprehensive and highly relevant information for answering the question:",
                'medium': "The following context contains relevant information that should help answer the question:",
                'low': "Limited relevant information was found. Based on the available context:",
                'none': "No directly relevant information was found in the knowledge base. I can only provide general guidance:"
            },

            # Response format instructions
            'format_instructions': {
                ResponseType.SHORT_ANSWER: "\n\nProvide a brief, direct answer (1-2 sentences maximum).",
                ResponseType.DETAILED_EXPLANATION: "\n\nProvide a comprehensive explanation with relevant details.",
                ResponseType.STEP_BY_STEP: "\n\nStructure your response as numbered steps. Be clear and sequential.",
                ResponseType.LIST: "\n\nProvide a bulleted or numbered list of all relevant items.",
                ResponseType.COMPARISON: "\n\nStructure your response to clearly compare and contrast the elements.",
                ResponseType.SUMMARY: "\n\nProvide a concise summary of the main points."
            },

            # Language instructions
            'language': {
                'italian': "\n\nRispondi in italiano usando un tono professionale ma accessibile.",
                'english': "\n\nRespond in English using a professional yet accessible tone.",
                'auto': "\n\nRespond in the same language as the query."
            },

            # Fallback handling
            'fallback': {
                'no_info': "\n\nImportant: If the context doesn't contain relevant information, clearly state this limitation and avoid speculation.",
                'partial_info': "\n\nNote: If some aspects of the question cannot be answered from the context, explicitly mention what information is missing.",
                'hallucination_guard': "\n\nCritical: Base your response ONLY on the provided context. Do not add information from general knowledge unless explicitly stating it as such."
            }
        }

    def generate_prompt(
        self,
        classification: QueryClassification,
        retrieved_chunks: List[Dict[str, Any]],
        retrieval_scores: List[float],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate an adaptive prompt based on query classification and retrieval quality.

        Args:
            classification: Query classification results
            retrieved_chunks: Retrieved document chunks
            retrieval_scores: Similarity scores for retrieved chunks
            conversation_history: Previous conversation turns

        Returns:
            Complete adaptive prompt for the LLM
        """
        # Calculate retrieval quality
        retrieval_quality = self._assess_retrieval_quality(retrieval_scores)

        # Build prompt components
        components = []

        # 1. Base instruction based on intent
        base_instruction = self.templates['base_instruction'][classification.intent]
        components.append(base_instruction)

        # 2. Retrieval quality context
        quality_context = self.templates['retrieval_quality'][retrieval_quality]
        components.append(quality_context)

        # 3. Add retrieved context
        if retrieved_chunks:
            context_text = self._format_context(retrieved_chunks, retrieval_scores)
            components.append(f"\n\n=== CONTEXT ===\n{context_text}\n=== END CONTEXT ===")

        # 4. Add conversation history if contextual
        if classification.is_follow_up and conversation_history:
            history_text = self._format_history(conversation_history)
            components.append(f"\n\n=== CONVERSATION HISTORY ===\n{history_text}\n=== END HISTORY ===")

        # 5. Add the user query
        components.append(f"\n\nUser Question: {classification.query}")

        # 6. Add response format instructions
        format_instruction = self.templates['format_instructions'][classification.response_type]
        components.append(format_instruction)

        # 7. Add language instruction (detect from query)
        language = self._detect_language(classification.query)
        language_instruction = self.templates['language'][language]
        components.append(language_instruction)

        # 8. Add fallback guards based on retrieval quality
        if retrieval_quality == 'low':
            components.append(self.templates['fallback']['partial_info'])
        elif retrieval_quality == 'none':
            components.append(self.templates['fallback']['no_info'])

        # Always add hallucination guard
        components.append(self.templates['fallback']['hallucination_guard'])

        # Combine all components
        prompt = '\n'.join(components)

        # Add specific examples for certain query types
        prompt = self._add_examples_if_needed(prompt, classification)

        return prompt

    def _assess_retrieval_quality(self, scores: List[float]) -> str:
        """Assess overall retrieval quality based on similarity scores"""
        if not scores:
            return 'none'

        avg_score = sum(scores) / len(scores)
        top_score = max(scores) if scores else 0

        if top_score >= 0.7 and avg_score >= 0.5:
            return 'high'
        elif top_score >= 0.5 and avg_score >= 0.3:
            return 'medium'
        elif top_score >= 0.3:
            return 'low'
        else:
            return 'none'

    def _format_context(self, chunks: List[Dict[str, Any]], scores: List[float]) -> str:
        """Format retrieved chunks with relevance indicators"""
        formatted_chunks = []

        for i, (chunk, score) in enumerate(zip(chunks, scores)):
            relevance = "HIGH" if score >= 0.7 else "MEDIUM" if score >= 0.5 else "LOW"

            # Extract text from chunk (handle different formats)
            if isinstance(chunk, dict):
                text = chunk.get('text', chunk.get('content', str(chunk)))
                metadata = chunk.get('metadata', {})
                source = metadata.get('source', f'Document {i+1}')
            else:
                text = str(chunk)
                source = f'Document {i+1}'

            formatted_chunks.append(
                f"[Source: {source} | Relevance: {relevance}]\n{text}"
            )

        return "\n\n---\n\n".join(formatted_chunks)

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history"""
        formatted = []
        for turn in history[-3:]:  # Last 3 turns for context
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')
            formatted.append(f"{role.upper()}: {content}")

        return "\n".join(formatted)

    def _detect_language(self, query: str) -> str:
        """Simple language detection based on common words"""
        italian_indicators = ['come', 'cosa', 'quale', 'quando', 'dove', 'perché',
                             'ricetta', 'ingredienti', 'preparare', 'è', 'sono']

        query_lower = query.lower()
        italian_count = sum(1 for word in italian_indicators if word in query_lower)

        if italian_count >= 2:
            return 'italian'
        else:
            return 'auto'  # Let the model decide

    def _add_examples_if_needed(self, prompt: str, classification: QueryClassification) -> str:
        """Add specific examples for certain complex query types"""
        if classification.intent == QueryIntent.PROCEDURAL and 'recipe' in classification.domain_indicators:
            example = """

Example of expected format for recipe:
INGREDIENTI:
- [List ingredients with quantities]

PREPARAZIONE:
1. [First step]
2. [Second step]
...

CONSIGLI:
- [Optional tips]"""
            return prompt + example

        return prompt


class AdaptiveQueryProcessor:
    """
    Main orchestrator that combines classification and prompt generation.
    Integrates with the existing query_engine.py.
    """

    def __init__(self):
        self.classifier = QueryClassifier()
        self.prompt_generator = AdaptivePromptGenerator()
        self.metrics = QueryMetrics()

    def process_query(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        retrieval_scores: List[float],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, QueryClassification]:
        """
        Process a query end-to-end: classify and generate adaptive prompt.

        Args:
            query: User query
            retrieved_chunks: Chunks from retrieval system
            retrieval_scores: Similarity scores
            conversation_history: Previous conversation

        Returns:
            Tuple of (adaptive_prompt, classification)
        """
        # Step 1: Classify the query
        classification = self.classifier.classify(query, conversation_history)

        # Log classification for debugging
        logger.info(f"Query classified as: Intent={classification.intent.value}, "
                   f"Specificity={classification.specificity.value}, "
                   f"Response={classification.response_type.value}")

        # Step 2: Generate adaptive prompt
        prompt = self.prompt_generator.generate_prompt(
            classification,
            retrieved_chunks,
            retrieval_scores,
            conversation_history
        )

        # Step 3: Track metrics
        self.metrics.record_query(classification, retrieval_scores)

        return prompt, classification

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of query processing metrics"""
        return self.metrics.get_summary()


class QueryMetrics:
    """Track metrics for query processing effectiveness"""

    def __init__(self):
        self.queries = []
        self.intent_counts = {}
        self.retrieval_qualities = []

    def record_query(self, classification: QueryClassification, retrieval_scores: List[float]):
        """Record metrics for a processed query"""
        self.queries.append({
            'intent': classification.intent.value,
            'specificity': classification.specificity.value,
            'confidence': classification.confidence,
            'retrieval_avg': sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0,
            'retrieval_max': max(retrieval_scores) if retrieval_scores else 0
        })

        # Update intent counts
        intent = classification.intent.value
        self.intent_counts[intent] = self.intent_counts.get(intent, 0) + 1

        # Track retrieval quality
        if retrieval_scores:
            avg_score = sum(retrieval_scores) / len(retrieval_scores)
            self.retrieval_qualities.append(avg_score)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        if not self.queries:
            return {'total_queries': 0}

        return {
            'total_queries': len(self.queries),
            'intent_distribution': self.intent_counts,
            'avg_classification_confidence': sum(q['confidence'] for q in self.queries) / len(self.queries),
            'avg_retrieval_quality': sum(self.retrieval_qualities) / len(self.retrieval_qualities) if self.retrieval_qualities else 0,
            'retrieval_quality_distribution': {
                'high': sum(1 for q in self.retrieval_qualities if q >= 0.7),
                'medium': sum(1 for q in self.retrieval_qualities if 0.4 <= q < 0.7),
                'low': sum(1 for q in self.retrieval_qualities if q < 0.4)
            }
        }