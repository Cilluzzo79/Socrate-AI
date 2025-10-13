"""
Simple direct debug utility for Memvid document retrieval.
Tests whether metadata files are found and used during retrieval.
"""

import os
import sys
import json
import time
from pathlib import Path

# Fixed output directory for Memvid documents
OUTPUT_DIR = "D:\\railway\\memvid\\memvidBeta\\encoder_app\\outputs"
LOG_FILE = "debug_log.txt"

def log(message):
    """Write message to both console and log file"""
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def clear_log():
    """Clear the log file"""
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=== MEMVID DEBUG LOG ===\n\n")

def check_document_files(doc_name):
    """
    Check what files exist for the specified document name.
    """
    log(f"\n=== CHECKING FILES FOR DOCUMENT: {doc_name} ===")
    
    # Try both in the current directory and in outputs
    directories_to_check = [
        OUTPUT_DIR,  # Primary location - fixed path
        ".",         # Current directory as fallback
    ]
    
    for directory in directories_to_check:
        if not os.path.exists(directory):
            log(f"Directory does not exist: {directory}")
            continue
            
        log(f"Checking directory: {directory}")
        
        # List files in the directory
        files = os.listdir(directory)
        
        # Filter files related to the document
        related_files = [f for f in files if doc_name in f]
        
        if related_files:
            log(f"Found {len(related_files)} files related to {doc_name}:")
            
            for file in related_files:
                file_path = os.path.join(directory, file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                log(f"  - {file} ({file_size:.2f} KB)")
                
                # For JSON files, check their structure
                if file.endswith(".json"):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        
                        log(f"    JSON structure for {file}:")
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if isinstance(value, list):
                                    log(f"      {key}: list with {len(value)} items")
                                    
                                    # For chunks, check a sample
                                    if key == "chunks" and len(value) > 0:
                                        sample_chunk = value[0]
                                        log(f"      Sample chunk keys: {', '.join(sample_chunk.keys())}")
                                        
                                        # Check for page information
                                        page_info_count = 0
                                        max_page = 0
                                        article_info_count = 0
                                        articles_found = set()
                                        
                                        log("      Scanning chunks for page and article info...")
                                        for chunk_idx, chunk in enumerate(value):
                                            # Check if chunk has page info in metadata
                                            if "metadata" in chunk and "page" in chunk["metadata"]:
                                                page_info_count += 1
                                                max_page = max(max_page, int(chunk["metadata"]["page"]))
                                            
                                            # Check if chunk text contains page markers
                                            if "text" in chunk:
                                                text = chunk["text"].lower()
                                                
                                                # Look for page markers
                                                if "## pagina" in text or "page" in text:
                                                    page_info_count += 1
                                                
                                                # Look for article references
                                                if "articolo" in text or "art." in text:
                                                    article_info_count += 1
                                                    
                                                    # Extract article numbers (basic pattern matching)
                                                    import re
                                                    article_patterns = [
                                                        r"articolo\s+(\d+)",
                                                        r"art\.\s+(\d+)",
                                                        r"art\s+(\d+)"
                                                    ]
                                                    
                                                    for pattern in article_patterns:
                                                        matches = re.finditer(pattern, text, re.IGNORECASE)
                                                        for match in matches:
                                                            article_num = match.group(1)
                                                            articles_found.add(article_num)
                                                            
                                                # Check specifically for Article 32
                                                if "articolo 32" in text or "art. 32" in text or "art 32" in text:
                                                    log(f"      *** FOUND ARTICLE 32 in chunk {chunk_idx} ***")
                                                    text_preview = text[:100].replace("\n", " ") + "..."
                                                    log(f"      Text preview: {text_preview}")
                                        
                                        log(f"      Page info found in {page_info_count} chunks, max page: {max_page}")
                                        log(f"      Article references found in {article_info_count} chunks")
                                        log(f"      Articles found: {', '.join(sorted(articles_found))}")
                                    
                                elif isinstance(value, dict):
                                    log(f"      {key}: dict with {len(value)} keys")
                                else:
                                    log(f"      {key}: {type(value).__name__}")
                        else:
                            log(f"      JSON data is a {type(data).__name__}, not a dict")
                    
                    except Exception as e:
                        log(f"    Error parsing JSON: {str(e)}")
            
            return directory, related_files
        
    log(f"No files found for document: {doc_name}")
    return None, []

def test_retrieval_manually(doc_name, query="articolo 32"):
    """
    Manually test retrieval without using the actual retrieval function.
    This is a simplified simulation to see what data would be available.
    """
    log(f"\n=== MANUAL RETRIEVAL TEST FOR: {doc_name}, QUERY: '{query}' ===")
    
    directory, related_files = check_document_files(doc_name)
    if not directory:
        log("Cannot test retrieval - no files found")
        return
    
    # Look for metadata and index files
    metadata_file = None
    index_file = None
    
    for file in related_files:
        if "metadata" in file and file.endswith(".json"):
            metadata_file = os.path.join(directory, file)
        elif "index.json" in file:
            index_file = os.path.join(directory, file)
    
    log(f"Metadata file: {metadata_file}")
    log(f"Index file: {index_file}")
    
    # Check both files for the query
    query_lower = query.lower()
    results = []
    
    if metadata_file and os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            if "chunks" in metadata and isinstance(metadata["chunks"], list):
                log(f"Searching through {len(metadata['chunks'])} chunks in metadata file...")
                
                for i, chunk in enumerate(metadata["chunks"]):
                    if "text" in chunk and isinstance(chunk["text"], str):
                        if query_lower in chunk["text"].lower():
                            log(f"Found query in chunk {i} of metadata file")
                            
                            # Get score (simulated)
                            score = 0.95  # High score for exact match
                            
                            # Get metadata
                            chunk_metadata = chunk.get("metadata", {})
                            
                            # Create result
                            results.append({
                                "text": chunk["text"],
                                "score": score,
                                "source": "metadata_file",
                                "metadata": chunk_metadata,
                                "chunk_index": i
                            })
        except Exception as e:
            log(f"Error searching metadata file: {str(e)}")
    
    if index_file and os.path.exists(index_file):
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
            
            if "documents" in index_data and isinstance(index_data["documents"], list):
                log(f"Searching through {len(index_data['documents'])} documents in index file...")
                
                for i, doc in enumerate(index_data["documents"]):
                    if "text" in doc and isinstance(doc["text"], str):
                        if query_lower in doc["text"].lower():
                            log(f"Found query in document {i} of index file")
                            
                            # Get score (simulated)
                            score = 0.90  # High score for exact match
                            
                            # Get metadata
                            doc_metadata = doc.get("metadata", {})
                            
                            # Create result
                            results.append({
                                "text": doc["text"],
                                "score": score,
                                "source": "index_file",
                                "metadata": doc_metadata,
                                "doc_index": i
                            })
        except Exception as e:
            log(f"Error searching index file: {str(e)}")
    
    # Display results
    log(f"\nFound {len(results)} results for query: '{query}'")
    
    for i, result in enumerate(results):
        log(f"\nResult {i+1} from {result['source']}:")
        log(f"Score: {result['score']}")
        
        # Display metadata
        log("Metadata:")
        for key, value in result.get("metadata", {}).items():
            if isinstance(value, (list, dict)):
                log(f"  - {key}: {type(value).__name__} with {len(value)} items")
            else:
                log(f"  - {key}: {value}")
        
        # Show text preview (first 200 chars)
        text_preview = result["text"][:200].replace("\n", " ") + "..."
        log(f"Text preview: {text_preview}")

def main():
    """Main function"""
    clear_log()
    log("=== MEMVID DOCUMENT DEBUG ===")
    log(f"Current directory: {os.getcwd()}")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        doc_name = sys.argv[1]
    else:
        doc_name = "TUIR_2025_sections"
    
    # Check document files
    check_document_files(doc_name)
    
    # Test retrieval
    test_retrieval_manually(doc_name, "articolo 32")
    test_retrieval_manually(doc_name, "pagina 151")
    test_retrieval_manually(doc_name, "pagina 170")
    test_retrieval_manually(doc_name, "ultima pagina")

if __name__ == "__main__":
    main()
