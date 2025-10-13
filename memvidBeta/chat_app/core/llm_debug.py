"""
Debug interceptor for the LLM client to see exactly what's being sent to Claude.
This allows us to inspect the context and query before they reach the LLM.
"""

# Create a wrapper for the generate_chat_response function
from core.llm_client import generate_chat_response as original_generate_chat_response
import json
import os
import time

# Directory for debug logs
DEBUG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug_logs")
os.makedirs(DEBUG_DIR, exist_ok=True)

def generate_chat_response_with_debug(*args, **kwargs):
    """
    Wrapper around generate_chat_response that logs the input and output.
    """
    # Extract arguments
    query = kwargs.get('query', args[0] if args else None)
    context = kwargs.get('context', args[1] if len(args) > 1 else None)
    conversation_history = kwargs.get('conversation_history', args[2] if len(args) > 2 else None)
    document_metadata = kwargs.get('document_metadata', args[5] if len(args) > 5 else None)
    
    # Create debug log
    timestamp = int(time.time())
    debug_data = {
        "timestamp": timestamp,
        "query": query,
        "context_length": len(context) if context else 0,
        "context_preview": context[:1000] + "..." if context and len(context) > 1000 else context,
        "full_context": context,
        "history_length": len(conversation_history) if conversation_history else 0,
        "document_metadata": document_metadata
    }
    
    # Save to file
    debug_file = os.path.join(DEBUG_DIR, f"llm_input_{timestamp}.json")
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(debug_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[DEBUG] Saved LLM input to {debug_file}")
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] Context length: {debug_data['context_length']} characters")
    
    if context:
        context_parts = context.split("---")
        print(f"[DEBUG] Context has {len(context_parts)} parts (chunks)")
        
        for i, part in enumerate(context_parts):
            if part.strip():
                preview = part.strip()[:100] + "..." if len(part) > 100 else part.strip()
                print(f"[DEBUG] Chunk {i+1} preview: {preview}")
    
    # Call the original function
    result = original_generate_chat_response(*args, **kwargs)
    
    # Log the result
    debug_data["response"] = result
    debug_file_out = os.path.join(DEBUG_DIR, f"llm_output_{timestamp}.json")
    with open(debug_file_out, "w", encoding="utf-8") as f:
        json.dump(debug_data, f, indent=2, ensure_ascii=False)
    
    print(f"[DEBUG] Saved LLM output to {debug_file_out}")
    print(f"[DEBUG] Response preview: {result['text'][:100]}...")
    
    return result


# Replace the original function with the debug version
import core.llm_client
core.llm_client.generate_chat_response = generate_chat_response_with_debug
