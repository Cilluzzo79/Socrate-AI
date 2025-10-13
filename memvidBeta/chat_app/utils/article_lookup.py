"""
Custom handler for specific article queries in the bot.
This module provides a direct lookup function for articles in the TUIR document.
"""

import re
import os
from pathlib import Path
import json
from typing import Dict, List, Optional, Tuple, Any

# Configure paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
ENCODER_APP_DIR = os.path.join(BASE_DIR, "encoder_app")
OUTPUTS_DIR = os.path.join(ENCODER_APP_DIR, "outputs")


def find_article_in_tuir(article_number: str) -> Optional[str]:
    """
    Find a specific article in the TUIR document.
    Directly accesses the metadata files to find the article text.
    
    Args:
        article_number: The article number to find (as a string)
        
    Returns:
        Optional[str]: The article text if found, None otherwise
    """
    # Find the TUIR metadata file
    metadata_file = None
    for file in os.listdir(OUTPUTS_DIR):
        if "TUIR" in file and file.endswith("_metadata.json"):
            metadata_file = os.path.join(OUTPUTS_DIR, file)
            break
    
    if not metadata_file:
        print("Could not find TUIR metadata file!")
        return None
    
    print(f"Looking for article {article_number} in {metadata_file}")
    
    # Load the metadata
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        chunks = metadata.get('chunks', [])
        if not chunks:
            print("No chunks found in metadata file!")
            return None
            
        print(f"Loaded {len(chunks)} chunks from metadata file")
        
        # Find chunks that contain the article header
        article_chunks = []
        pattern = fr"(?:art(?:\.|icolo)?\s*{article_number}\.?|articolo\s*{article_number}\.?)"
        
        # First look for the exact article header
        for i, chunk in enumerate(chunks):
            if 'text' not in chunk:
                continue
                
            text = chunk['text'].lower()
            if re.search(pattern, text):
                article_chunks.append((i, chunk))
                print(f"Found reference to article {article_number} in chunk {i}")
        
        if not article_chunks:
            print(f"No references to article {article_number} found!")
            return None
        
        # Find the most likely chunk that contains the article header
        best_chunk = None
        for i, chunk in article_chunks:
            text = chunk['text'].lower()
            # Look for patterns like "art. 32. reddito agrario"
            if re.search(fr"art\.\s*{article_number}\.\s", text) or re.search(fr"articolo\s*{article_number}\.\s", text):
                print(f"Found article {article_number} header in chunk {i}")
                best_chunk = chunk
                break
        
        if best_chunk:
            # Extract all relevant chunks that continue the article
            article_text = best_chunk['text']
            
            # Sort remaining chunks by position
            remaining_chunks = [(i, c) for i, c in article_chunks if c != best_chunk]
            if all('metadata' in c and 'start' in c['metadata'] for _, c in remaining_chunks):
                remaining_chunks.sort(key=lambda x: x[1]['metadata']['start'])
            
            # Add up to 3 more chunks to get the full article
            for i, chunk in remaining_chunks[:3]:
                article_text += "\n\n" + chunk['text']
            
            print(f"Extracted article {article_number} text with {len(article_text)} characters")
            return article_text
        
        # If we can't find the exact header, just return all chunks that mention the article
        article_text = ""
        for i, chunk in article_chunks[:4]:  # Limit to 4 chunks
            if article_text:
                article_text += "\n\n"
            article_text += chunk['text']
        
        print(f"Extracted article {article_number} references with {len(article_text)} characters")
        return article_text
            
    except Exception as e:
        print(f"Error finding article: {e}")
        return None


def get_article_as_context(article_number: str) -> str:
    """
    Get the article text formatted as a context string for the LLM.
    
    Args:
        article_number: The article number to find
        
    Returns:
        str: The formatted context string
    """
    article_text = find_article_in_tuir(article_number)
    
    if not article_text:
        return "Articolo non trovato nel TUIR."
    
    # Format the context with a clear header
    context = f"[Articolo {article_number} del TUIR]\n\n{article_text}"
    
    return context


def handle_article_query(query: str) -> Optional[str]:
    """
    Check if a query is asking for a specific article and return the article text if it is.
    
    Args:
        query: The user query
        
    Returns:
        Optional[str]: The article context if it's an article query, None otherwise
    """
    # Check if the query is asking for a specific article
    article_match = re.search(r'articolo\s+(\d+)', query.lower())
    
    if article_match:
        article_number = article_match.group(1)
        return get_article_as_context(article_number)
    
    return None
