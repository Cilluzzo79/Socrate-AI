"""
Embedding Generator
Pre-computes embeddings and FAISS index during document processing
"""

import os
import json
import logging
import numpy as np
from typing import Tuple, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import sentence-transformers and faiss
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    EMBEDDINGS_AVAILABLE = True
except ImportError as e:
    EMBEDDINGS_AVAILABLE = False
    logger.warning(f"Embeddings libraries not available: {e}")


def generate_and_save_embeddings(
    metadata_file: str,
    output_dir: str,
    document_id: str,
    model_name: str = 'all-MiniLM-L6-v2',
    batch_size: int = 16,  # Reduced from 32 to 16 for memory
    max_chunks_per_batch: int = 100  # Process in smaller groups
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generate embeddings for all chunks and create FAISS index

    Args:
        metadata_file: Path to metadata JSON file
        output_dir: Directory to save embeddings and index
        document_id: Document UUID
        model_name: Sentence transformer model to use
        batch_size: Batch size for encoding

    Returns:
        Tuple of (embeddings_file_path, faiss_index_path) or (None, None) if failed
    """

    if not EMBEDDINGS_AVAILABLE:
        logger.warning("Embeddings libraries not available, skipping")
        return None, None

    try:
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        chunks = metadata.get('chunks', [])
        if not chunks:
            logger.warning("No chunks found in metadata")
            return None, None

        num_chunks = len(chunks)
        logger.info(f"Generating embeddings for {num_chunks} chunks...")

        # Load model
        logger.info(f"Loading sentence transformer model: {model_name}")
        model = SentenceTransformer(model_name)

        # Process in smaller groups to avoid OOM
        all_embeddings = []
        num_groups = (num_chunks + max_chunks_per_batch - 1) // max_chunks_per_batch

        logger.info(f"Processing {num_chunks} chunks in {num_groups} groups of max {max_chunks_per_batch}")

        for group_idx in range(num_groups):
            start_idx = group_idx * max_chunks_per_batch
            end_idx = min(start_idx + max_chunks_per_batch, num_chunks)

            logger.info(f"Group {group_idx + 1}/{num_groups}: Processing chunks {start_idx}-{end_idx}")

            # Extract chunk texts for this group
            chunk_texts_group = [chunks[i]['text'] for i in range(start_idx, end_idx)]

            # Generate embeddings for this group
            embeddings_group = model.encode(
                chunk_texts_group,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True
            )

            all_embeddings.append(embeddings_group)

            # Force garbage collection after each group
            import gc
            chunk_texts_group = None
            embeddings_group = None
            gc.collect()

            logger.info(f"Group {group_idx + 1}/{num_groups} completed, memory cleaned")

        # Combine all embeddings
        embeddings = np.vstack(all_embeddings)
        all_embeddings = None  # Free memory
        import gc
        gc.collect()

        logger.info(f"Generated embeddings shape: {embeddings.shape}")

        # Save embeddings as numpy array
        embeddings_file = os.path.join(output_dir, f"{document_id}_embeddings.npy")
        np.save(embeddings_file, embeddings)
        logger.info(f"Embeddings saved to: {embeddings_file}")

        # Create FAISS index for fast similarity search
        logger.info("Creating FAISS index...")
        dimension = embeddings.shape[1]

        # Use IndexFlatIP for cosine similarity (after normalization)
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        index = faiss.IndexFlatIP(dimension)  # Inner product = cosine after normalization
        index.add(embeddings)

        logger.info(f"FAISS index created with {index.ntotal} vectors")

        # Save FAISS index
        faiss_file = os.path.join(output_dir, f"{document_id}_index.faiss")
        faiss.write_index(index, faiss_file)
        logger.info(f"FAISS index saved to: {faiss_file}")

        return embeddings_file, faiss_file

    except Exception as e:
        logger.error(f"Error generating embeddings: {e}", exc_info=True)
        return None, None


def load_precomputed_embeddings(embeddings_path: str) -> Optional[np.ndarray]:
    """
    Load pre-computed embeddings from file

    Args:
        embeddings_path: Path to .npy file

    Returns:
        Numpy array of embeddings or None if failed
    """
    try:
        embeddings = np.load(embeddings_path)
        logger.info(f"Loaded embeddings: {embeddings.shape}")
        return embeddings
    except Exception as e:
        logger.error(f"Error loading embeddings from {embeddings_path}: {e}")
        return None


def load_faiss_index(faiss_path: str):
    """
    Load FAISS index from file

    Args:
        faiss_path: Path to .faiss file

    Returns:
        FAISS index or None if failed
    """
    if not EMBEDDINGS_AVAILABLE:
        return None

    try:
        index = faiss.read_index(faiss_path)
        logger.info(f"Loaded FAISS index with {index.ntotal} vectors")
        return index
    except Exception as e:
        logger.error(f"Error loading FAISS index from {faiss_path}: {e}")
        return None


def search_similar_chunks(
    query_embedding: np.ndarray,
    faiss_index,
    top_k: int = 5
) -> Tuple[List[int], List[float]]:
    """
    Search for most similar chunks using FAISS index

    Args:
        query_embedding: Query embedding vector (normalized)
        faiss_index: FAISS index
        top_k: Number of results to return

    Returns:
        Tuple of (indices, scores) for top-k most similar chunks
    """
    try:
        # Normalize query embedding for cosine similarity
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)

        # Search
        scores, indices = faiss_index.search(query_embedding, top_k)

        # Convert to lists
        indices_list = indices[0].tolist()
        scores_list = scores[0].tolist()

        return indices_list, scores_list

    except Exception as e:
        logger.error(f"Error searching FAISS index: {e}")
        return [], []
