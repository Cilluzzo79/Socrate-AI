# Adaptive Query Understanding & Prompting System

## Overview

This system provides **end-to-end adaptive RAG** with two key components:
1. **Adaptive Retrieval** - Dynamically adjusts retrieval strategy based on query needs
2. **Adaptive Prompting** - Generates context-aware prompts for optimal LLM responses

Together, they create a RAG pipeline that understands not just *what* to retrieve, but *how* to present it to the LLM for the best possible answer.

## Key Features

### 1. Query Classification
The system analyzes each query across multiple dimensions:

- **Intent** (6 types):
  - `FACTUAL` - Looking for specific facts
  - `PROCEDURAL` - How-to questions
  - `EXPLORATORY` - Browsing/discovery queries
  - `ANALYTICAL` - Comparison, analysis, reasoning
  - `DEFINITIONAL` - What is X?
  - `CONTEXTUAL` - Follow-up questions

- **Specificity**:
  - `SPECIFIC` - Narrow, focused query
  - `MODERATE` - Balanced scope
  - `BROAD` - Wide-ranging query

- **Response Type**:
  - `SHORT_ANSWER` - Brief, direct answer
  - `DETAILED_EXPLANATION` - Comprehensive explanation
  - `STEP_BY_STEP` - Sequential instructions
  - `LIST` - Enumerated items
  - `COMPARISON` - Compare/contrast
  - `SUMMARY` - Concise overview

### 2. Adaptive Prompt Generation

Based on classification, the system generates prompts that:
- Set appropriate response style and length
- Guide the LLM on how to use retrieved chunks
- Adjust tone and formality
- Handle edge cases (no/partial information)

### 3. Retrieval Quality Awareness

The prompt adapts based on retrieval quality:
- **HIGH (0.7+)**: "You have comprehensive information..."
- **MEDIUM (0.4-0.7)**: "Based on available information..."
- **LOW (<0.4)**: "Limited information found..."
- **NONE**: "No relevant information found..."

## Architecture

```
User Query
    ↓
[Query Classifier]
    ↓
Query Classification
    ├── Intent
    ├── Specificity
    └── Response Type
    ↓
[Adaptive Retriever] ←→ [Vector Store + BM25]
    ↓
Retrieved Chunks + Scores
    ↓
[Adaptive Prompt Generator]
    ↓
Tailored System Prompt
    ↓
[LLM]
    ↓
Optimized Response
```

## Quick Start

### 1. Basic Usage

```python
from core.adaptive_query_engine import create_adaptive_engine
from core.llm_client import LLMClient

# Initialize components
engine = create_adaptive_engine(
    vector_store=your_vector_store,
    bm25_index=your_bm25_index,
    llm_client=LLMClient()
)

# Process a query
result = engine.query("Come si prepara l'ossobuco alla milanese?")

# Access detailed results
print(f"Answer: {result.llm_response}")
print(f"Intent: {result.classification.intent}")
print(f"Strategy Used: {result.retrieval_strategy}")
print(f"Retrieval Quality: {result.metadata['retrieval_quality']}")
```

### 2. Upgrading Existing Query Engine

```python
from core.query_engine_integration import upgrade_existing_engine

# Your existing engine
old_engine = QueryEngine(...)

# Upgrade to adaptive
adaptive_engine = upgrade_existing_engine(old_engine)

# Use the same interface
result = adaptive_engine.query("Quali ricette ci sono?")
```

### 3. Using Configuration Presets

```python
from core.query_engine_integration import get_preset_config, IntegratedQueryEngine

# Choose a preset based on your needs
config = get_preset_config('high_precision')  # or 'high_recall', 'balanced', 'fast'

engine = IntegratedQueryEngine(**config)
```

## Example Scenarios

### Scenario 1: Specific Recipe Query
```python
query = "Come si prepara l'ossobuco alla milanese?"
```
- **Classification**: Intent=PROCEDURAL, Specificity=SPECIFIC, Response=STEP_BY_STEP
- **Retrieval**: Starts with k=10, looks for high-similarity chunks
- **Prompt**: Guides LLM to structure as: Ingredients → Steps → Tips

### Scenario 2: Broad Exploration
```python
query = "Quali ricette ci sono nel documento?"
```
- **Classification**: Intent=EXPLORATORY, Specificity=BROAD, Response=LIST
- **Retrieval**: Starts with k=20, accepts lower similarity threshold
- **Prompt**: Guides LLM to list ALL items found

### Scenario 3: Analytical Comparison
```python
query = "Qual è la differenza tra ossobuco milanese e fiorentino?"
```
- **Classification**: Intent=ANALYTICAL, Specificity=SPECIFIC, Response=COMPARISON
- **Retrieval**: Retrieves chunks about both variants
- **Prompt**: Guides LLM to compare/contrast

### Scenario 4: Follow-up Query
```python
query = "E quanto tempo ci vuole?"  # After previous recipe question
```
- **Classification**: Intent=CONTEXTUAL, Is_follow_up=True
- **Retrieval**: Limited retrieval, relies on conversation context
- **Prompt**: Includes conversation history for context

## Configuration Options

### Per-Intent Retrieval Settings

```python
config = {
    'retrieval_config': {
        QueryIntent.FACTUAL: {
            'initial_k': 5,
            'fallback_multiplier': 2,
            'quality_threshold': 0.7
        },
        QueryIntent.EXPLORATORY: {
            'initial_k': 20,  # Cast wide net
            'fallback_multiplier': 1.5,
            'quality_threshold': 0.4
        },
        # ... more intents
    }
}
```

### LLM Parameters by Response Type

```python
config = {
    'llm_config': {
        'temperature': {
            'SHORT_ANSWER': 0.1,      # Precise
            'DETAILED_EXPLANATION': 0.3,  # Some creativity
            'COMPARISON': 0.3,         # Analytical flexibility
        },
        'max_tokens': {
            'SHORT_ANSWER': 150,
            'DETAILED_EXPLANATION': 1000,
            'STEP_BY_STEP': 800,
        }
    }
}
```

## Advanced Features

### 1. Conversation Context

The system maintains conversation history for contextual queries:

```python
# Clear history for new conversation
engine.clear_conversation_history()

# First query
result1 = engine.query("Come si prepara il risotto?")

# Follow-up uses context
result2 = engine.query("Quanto tempo ci vuole?")  # Knows we're talking about risotto
```

### 2. Domain Detection

Automatically detects domain-specific terminology:
- Recipe: 'ricetta', 'ingredienti', 'cottura'
- Technical: 'configurazione', 'sistema', 'API'
- Medical: 'sintomi', 'diagnosi', 'terapia'
- Legal: 'contratto', 'legge', 'articolo'

### 3. Fallback Handling

When retrieval quality is low:
- Adjusts LLM temperature (more conservative)
- Adds explicit warnings about limited information
- Prevents hallucination with strict prompts

## Metrics and Monitoring

```python
# Get processing metrics
metrics = engine.get_metrics()

print(f"Total Queries: {metrics['total_queries']}")
print(f"Intent Distribution: {metrics['intent_distribution']}")
print(f"Avg Retrieval Quality: {metrics['avg_retrieval_quality']:.2f}")
print(f"Quality Distribution: {metrics['retrieval_quality_distribution']}")
```

## Testing

Run the test suite to see all features in action:

```bash
python test_adaptive_prompting.py
```

This demonstrates:
- Query classification accuracy
- Prompt adaptation based on retrieval quality
- Conversation context handling
- Domain detection
- Response type detection

## Files Overview

- **`core/query_classifier.py`** - Query classification and prompt generation
- **`core/adaptive_query_engine.py`** - Complete adaptive engine
- **`core/adaptive_retrieval.py`** - Adaptive retrieval strategies
- **`core/query_engine_integration.py`** - Integration with existing systems
- **`test_adaptive_prompting.py`** - Comprehensive test suite

## Best Practices

1. **Let the system classify first** - Don't override classification unless necessary
2. **Monitor retrieval quality** - Low quality may indicate need for better chunking
3. **Use conversation history** - Especially important for chatbot interfaces
4. **Choose appropriate presets** - High precision for factual, high recall for exploration
5. **Test with your data** - Run the test suite with your actual documents

## Troubleshooting

### Issue: Poor intent classification
- **Solution**: Add domain-specific patterns to `QueryClassifier.intent_patterns`

### Issue: Retrieved chunks not relevant
- **Solution**: Adjust quality thresholds in retrieval config

### Issue: LLM responses too verbose/brief
- **Solution**: Modify `max_tokens` in LLM config for response types

### Issue: Follow-up queries losing context
- **Solution**: Ensure conversation history is being maintained

## Performance Considerations

- Query classification is lightweight (pattern matching)
- Adaptive retrieval may do multiple searches (trade-off for quality)
- Prompt generation adds minimal overhead
- LLM generation time depends on response type settings

## Next Steps

1. **Fine-tune for your domain** - Add domain-specific patterns
2. **Optimize retrieval parameters** - Based on your data characteristics
3. **Customize prompt templates** - For your specific use cases
4. **Monitor and iterate** - Use metrics to identify areas for improvement

The adaptive system is designed to be flexible and extensible. Start with the defaults, measure performance, and adjust based on your specific needs.