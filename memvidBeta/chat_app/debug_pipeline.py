"""
Enhanced debug script that creates a full dump of the retrieval pipeline,
showing every step of the process from query to LLM input.
"""

import sys
import os
import re
import json
import datetime
from pathlib import Path

# Set up directory for debug logs
script_dir = os.path.dirname(os.path.abspath(__file__))
debug_dir = os.path.join(script_dir, "full_pipeline_debug")
os.makedirs(debug_dir, exist_ok=True)

# Generate a timestamp for log files
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def debug_wrap(func_name):
    """Decorator to wrap functions for debugging"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Log start with parameters
            log_file = os.path.join(debug_dir, f"{timestamp}_{func_name}.log")
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"CALLING {func_name} at {datetime.datetime.now()}\n")
                f.write(f"Args: {args}\n")
                f.write(f"Kwargs: {kwargs}\n")
                f.write(f"{'='*50}\n\n")
            
            # Call the original function
            result = func(*args, **kwargs)
            
            # Log the result
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"RESULT from {func_name} at {datetime.datetime.now()}\n")
                
                # Different formatting based on result type
                if isinstance(result, (list, tuple)):
                    f.write(f"Result type: {type(result).__name__}, length: {len(result)}\n")
                    for i, item in enumerate(result):
                        f.write(f"Item {i}:\n{item}\n\n")
                elif isinstance(result, dict):
                    f.write(f"Result type: dict, keys: {result.keys()}\n")
                    f.write(f"Content: {json.dumps(result, indent=2, default=str)}\n")
                else:
                    f.write(f"Result type: {type(result).__name__}\n")
                    f.write(f"Result: {result}\n")
                
                f.write(f"{'='*50}\n\n")
            
            return result
        return wrapper
    return decorator

# Now, let's patch key functions in the relevant modules

# First, import the modules that need to be patched
sys.path.insert(0, script_dir)

# Create the patch script
with open(os.path.join(debug_dir, f"{timestamp}_patch_info.txt"), 'w', encoding='utf-8') as f:
    f.write("Pipeline Debug Patches\n")
    f.write(f"Created at: {datetime.datetime.now()}\n\n")
    f.write("This patch adds extensive logging to key functions in the retrieval and LLM pipeline.\n")
    f.write("The logs will be saved in the 'full_pipeline_debug' directory.\n\n")
    f.write("Patched functions:\n")
    f.write("- core.memvid_retriever.get_context_for_query\n")
    f.write("- core.memvid_retriever.format_context_for_llm\n") 
    f.write("- core.rag_pipeline.perform_hybrid_search\n")
    f.write("- core.rag_pipeline.process_query\n")
    f.write("- core.llm_client.generate_chat_response\n\n")

print(f"Patching functions for detailed debugging...")

# Import and patch memvid_retriever functions
try:
    from core.memvid_retriever import get_context_for_query, format_context_for_llm
    from core.rag_pipeline import perform_hybrid_search, process_query
    from core.llm_client import generate_chat_response
    
    # Store the original functions
    orig_get_context_for_query = get_context_for_query
    orig_format_context_for_llm = format_context_for_llm
    orig_perform_hybrid_search = perform_hybrid_search
    orig_process_query = process_query
    orig_generate_chat_response = generate_chat_response
    
    # Create wrapped versions
    @debug_wrap("get_context_for_query")
    def wrapped_get_context_for_query(*args, **kwargs):
        return orig_get_context_for_query(*args, **kwargs)
    
    @debug_wrap("format_context_for_llm")
    def wrapped_format_context_for_llm(*args, **kwargs):
        result = orig_format_context_for_llm(*args, **kwargs)
        # Save the full context to a separate file for easy inspection
        with open(os.path.join(debug_dir, f"{timestamp}_formatted_context.txt"), 'w', encoding='utf-8') as f:
            f.write(result)
        return result
    
    @debug_wrap("perform_hybrid_search")
    def wrapped_perform_hybrid_search(*args, **kwargs):
        return orig_perform_hybrid_search(*args, **kwargs)
    
    @debug_wrap("process_query")
    def wrapped_process_query(*args, **kwargs):
        return orig_process_query(*args, **kwargs)
    
    @debug_wrap("generate_chat_response")
    def wrapped_generate_chat_response(*args, **kwargs):
        return orig_generate_chat_response(*args, **kwargs)
    
    # Replace the original functions with the wrapped versions
    import core.memvid_retriever
    import core.rag_pipeline
    import core.llm_client
    
    core.memvid_retriever.get_context_for_query = wrapped_get_context_for_query
    core.memvid_retriever.format_context_for_llm = wrapped_format_context_for_llm
    core.rag_pipeline.perform_hybrid_search = wrapped_perform_hybrid_search
    core.rag_pipeline.process_query = wrapped_process_query
    core.llm_client.generate_chat_response = wrapped_generate_chat_response
    
    print("Successfully patched functions with debug wrappers!")
    
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Could not patch functions for debugging.")

print(f"Debug logs will be saved in: {debug_dir}")
print("Run the main application now to generate detailed debug logs.")
