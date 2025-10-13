"""
Direct script to extract and display the full text of Article 32 of the TUIR.
This script bypasses the regular search pipeline and directly accesses the metadata files.
"""

import sys
import os
from pathlib import Path
import json
import re

# Ensure we're in the right directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Define the location of metadata files
encoder_app_dir = os.path.join(os.path.dirname(script_dir), "encoder_app")
outputs_dir = os.path.join(encoder_app_dir, "outputs")

print(f"Looking for TUIR metadata in: {outputs_dir}")

# Search for TUIR files
tuir_files = []
for file in os.listdir(outputs_dir):
    if "TUIR" in file:
        tuir_files.append(file)

print(f"Found {len(tuir_files)} TUIR-related files: {', '.join(tuir_files)}")

# Try to find the metadata file
metadata_file = None
for file in tuir_files:
    if file.endswith("_metadata.json"):
        metadata_file = os.path.join(outputs_dir, file)
        break

if not metadata_file:
    print("Could not find TUIR metadata file!")
    sys.exit(1)

print(f"Loading metadata from: {metadata_file}")

# Load the metadata file
try:
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    print(f"Successfully loaded metadata file with {len(metadata.get('chunks', []))} chunks")
except Exception as e:
    print(f"Error loading metadata file: {e}")
    sys.exit(1)

# Function to extract article text
def extract_article_text(article_number, metadata):
    article_chunks = []
    article_pattern = fr"art(?:\.|icolo)?\s*{article_number}\b|articolo\s+{article_number}\b"
    
    # Find chunks that likely contain the article
    for i, chunk in enumerate(metadata.get('chunks', [])):
        if 'text' in chunk:
            text = chunk['text'].lower()
            if re.search(article_pattern, text):
                # Check if this chunk contains the article header
                if f"art. {article_number}." in text or f"articolo {article_number}." in text:
                    print(f"Found article {article_number} header in chunk {i}")
                    article_chunks.append((i, chunk))
    
    # If we found chunks with the article header
    if article_chunks:
        # Sort by position in the document
        if all('metadata' in chunk[1] and 'start' in chunk[1]['metadata'] for chunk in article_chunks):
            article_chunks.sort(key=lambda x: x[1]['metadata']['start'])
        
        # Create the full text
        full_text = ""
        for i, chunk in article_chunks:
            print(f"Adding chunk {i} to article text")
            chunk_text = chunk['text']
            
            # Check if we need to add separators
            if full_text and not full_text.endswith(("\n", ".", ":", ";")):
                full_text += "\n\n"
            
            full_text += chunk_text
    
        return full_text
    
    # If we didn't find the article header, try a broader search
    article_chunks = []
    for i, chunk in enumerate(metadata.get('chunks', [])):
        if 'text' in chunk and f"art. {article_number}" in chunk['text'].lower():
            print(f"Found article {article_number} reference in chunk {i}")
            article_chunks.append((i, chunk))
    
    if article_chunks:
        full_text = ""
        for i, chunk in article_chunks[:3]:  # Limit to first 3 chunks
            print(f"Adding chunk {i} to article text")
            chunk_text = chunk['text']
            if full_text:
                full_text += "\n\n"
            full_text += chunk_text
        
        return full_text
    
    return "Article not found"

# Extract Article 32
article_text = extract_article_text(32, metadata)

print("\n" + "="*80 + "\n")
print(f"ARTICLE 32 TEXT:\n\n{article_text}")
print("\n" + "="*80 + "\n")

# Create a clean version of the text to use in the chatbot
if article_text != "Article not found":
    print("Creating article output file...")
    
    with open("article_32.txt", "w", encoding="utf-8") as f:
        f.write(article_text)
    
    print(f"Article 32 text has been saved to {os.path.join(script_dir, 'article_32.txt')}")
    print("You can use this file to show the article text directly to users.")
