"""
Debug utility for testing Memvid retrieval.
Helps diagnose which JSON files are being used and how content is retrieved.
"""

import os
import sys
import json
from pathlib import Path
import time
import argparse

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, ".."))
sys.path.append(project_root)

# Import modules from the project
from core.memvid_retriever import get_retriever_manager, get_context_for_query, format_context_for_llm
from database.operations import get_document_by_id


def inspect_metadata_files(document_id):
    """
    Examine all metadata files related to a document.
    """
    print("\n=== METADATA FILES INSPECTION ===")
    
    # Get document from database
    document = get_document_by_id(document_id)
    if not document:
        print(f"Document with ID {document_id} not found in database.")
        return
    
    print(f"Document found: ID={document_id}")
    print(f"Video path: {document.video_path}")
    print(f"Index path: {document.index_path}")
    
    # Check various metadata files
    video_dir = os.path.dirname(document.video_path)
    base_name = os.path.splitext(os.path.basename(document.video_path))[0]
    
    potential_metadata_files = [
        os.path.join(video_dir, f"{base_name}_structure.json"),
        os.path.join(video_dir, f"{base_name}_simple_structure.json"),
        os.path.join(video_dir, f"{base_name}_light_metadata.json"),
        os.path.join(video_dir, f"{base_name}_smart_metadata.json"),
        os.path.join(video_dir, f"{base_name}_sections_metadata.json"),
        os.path.join(video_dir, f"{base_name}_metadata.json"),
        os.path.join(video_dir, f"{base_name}_debug_metadata.json"),
        os.path.join(video_dir, f"{base_name}_index.json")
    ]
    
    for metadata_file in potential_metadata_files:
        if os.path.exists(metadata_file):
            print(f"\nFound metadata file: {metadata_file}")
            print(f"Size: {os.path.getsize(metadata_file) / 1024:.2f} KB")
            
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"File type: JSON ({type(data).__name__})")
                
                # Analyze structure
                if isinstance(data, dict):
                    print("Top-level keys:")
                    for key in data.keys():
                        if isinstance(data[key], list):
                            print(f"  - {key}: list with {len(data[key])} items")
                        elif isinstance(data[key], dict):
                            print(f"  - {key}: dict with {len(data[key].keys())} keys")
                        else:
                            print(f"  - {key}: {type(data[key]).__name__}")
                    
                    # Check for chunks
                    if 'chunks' in data and isinstance(data['chunks'], list) and len(data['chunks']) > 0:
                        print(f"\nChunks: {len(data['chunks'])} total")
                        
                        # Sample first chunk
                        sample_chunk = data['chunks'][0]
                        print("Sample chunk keys:")
                        for key in sample_chunk.keys():
                            print(f"  - {key}")
                        
                        # Check for metadata
                        if 'metadata' in sample_chunk:
                            print("Sample chunk metadata keys:")
                            for key in sample_chunk['metadata'].keys():
                                print(f"  - {key}")
                        
                        # Check for page references
                        page_count = 0
                        max_page = 0
                        for chunk in data['chunks']:
                            if 'metadata' in chunk and 'page' in chunk['metadata']:
                                page_count += 1
                                max_page = max(max_page, chunk['metadata']['page'])
                            
                            # Also check text for page markers
                            elif 'text' in chunk:
                                if '## Pagina' in chunk['text'] or 'Page' in chunk['text']:
                                    page_count += 1
                        
                        print(f"\nPage references: Found in {page_count} chunks")
                        print(f"Highest page number found: {max_page}")
                
                # If it's the index file, look at the documents section
                if metadata_file.endswith('_index.json') and 'documents' in data:
                    print(f"\nIndex file contains {len(data['documents'])} documents")
                    if data['documents']:
                        sample_doc = data['documents'][0]
                        print("Sample document keys:")
                        for key in sample_doc.keys():
                            print(f"  - {key}")
                    
                    # Look for additional metadata
                    if 'metadata' in data:
                        print("\nIndex metadata:")
                        for key in data['metadata'].keys():
                            print(f"  - {key}")
                
            except Exception as e:
                print(f"Error analyzing file: {str(e)}")
        else:
            print(f"\nMetadata file not found: {metadata_file}")


def test_retrieval(document_id, query, top_k=5):
    """
    Test retrieval for a specific query and document.
    """
    print(f"\n=== TESTING RETRIEVAL FOR QUERY: '{query}' ===")
    
    # Get retriever manager and ensure it's loaded
    manager = get_retriever_manager()
    
    # Check if manager has metadata for this document
    if document_id in manager.metadata_cache:
        print(f"Document {document_id} has metadata in cache")
        
        # Check metadata structure
        metadata = manager.metadata_cache[document_id]
        print("Metadata top-level keys:")
        for key in metadata.keys():
            if isinstance(metadata[key], list):
                print(f"  - {key}: list with {len(metadata[key])} items")
            elif isinstance(metadata[key], dict):
                print(f"  - {key}: dict with {len(metadata[key].keys())} keys")
            else:
                print(f"  - {key}: {type(metadata[key]).__name__}")
    else:
        print(f"Document {document_id} has NO metadata in cache")
    
    # Test retrieval
    start_time = time.time()
    print(f"Retrieving with top_k={top_k}...")
    results = get_context_for_query(document_id, query, top_k=top_k)
    retrieval_time = time.time() - start_time
    
    print(f"Retrieved {len(results)} results in {retrieval_time:.2f} seconds")
    
    # Analyze results
    for i, result in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Score: {result.score:.4f}")
        
        # Check metadata
        print("Metadata:")
        for key, value in result.meta_info.items():
            if isinstance(value, (list, dict)):
                print(f"  - {key}: {type(value).__name__} ({len(value)} items)")
            else:
                print(f"  - {key}: {value}")
        
        # Display methods
        print(f"Title: {result.get_title()}")
        print(f"Position: {result.get_position_info()}")
        print(f"Path: {result.get_path()}")
        print(f"Page: {result.get_page_number()}")
        
        # Show text preview
        text_preview = result.text[:100].replace('\n', ' ').strip() + "..."
        print(f"Text preview: {text_preview}")
    
    # Format context for LLM
    formatted_context = format_context_for_llm(results)
    print(f"\nFormatted context length: {len(formatted_context)} characters")
    print("Formatted context preview:")
    print(formatted_context[:300].strip() + "...")


def main():
    parser = argparse.ArgumentParser(description="Debug Memvid retrieval")
    parser.add_argument("document_id", help="Document ID to test")
    parser.add_argument("--query", default="articolo 32", help="Test query (default: 'articolo 32')")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to retrieve (default: 5)")
    parser.add_argument("--inspect-only", action="store_true", help="Only inspect metadata files without testing retrieval")
    parser.add_argument("--inspect-all", action="store_true", help="Test retrieval with all available queries")
    
    args = parser.parse_args()
    
    # Inspect metadata files
    inspect_metadata_files(args.document_id)
    
    # Test retrieval if not in inspect-only mode
    if not args.inspect_only:
        test_retrieval(args.document_id, args.query, args.top_k)
    
    # Test additional queries if in inspect-all mode
    if args.inspect_all:
        additional_queries = [
            "ultima pagina",
            "pagina 170",
            "pagina 151",
            "struttura del documento",
            "articolo 159",
            "obblighi contabili"
        ]
        
        for query in additional_queries:
            print("\n" + "="*80)
            test_retrieval(args.document_id, query, args.top_k)


if __name__ == "__main__":
    main()
