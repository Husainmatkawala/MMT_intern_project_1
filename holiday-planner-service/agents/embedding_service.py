import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Embedding Service - Generate embeddings using sentence-transformers
    
    Responsibility: Centralized embedding generation for semantic similarity search
    Uses local transformer models (no API costs)
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize Embedding Service with sentence-transformers model
        
        Args:
            model_name (str): Name of the sentence-transformers model to use
                            Default: 'all-MiniLM-L6-v2' (384 dimensions, fast, good quality)
        """
        logger.info(f"Loading embedding model: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"Embedding model loaded successfully - Dimensions: {self.embedding_dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text (str): Input text to embed
            
        Returns:
            List[float]: Embedding vector
        """
        if not text or not isinstance(text, str):
            logger.warning(f"Invalid text input for embedding: {text}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dimension
        
        try:
            # Clean text
            text = text.strip()
            if not text:
                return [0.0] * self.embedding_dimension
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            # Convert to list for JSON serialization
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * self.embedding_dimension
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing for efficiency)
        
        Args:
            texts (List[str]): List of texts to embed
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not texts:
            logger.warning("Empty text list provided for batch embedding")
            return []
        
        try:
            # Clean texts
            cleaned_texts = []
            for text in texts:
                if text and isinstance(text, str):
                    cleaned_text = text.strip()
                    cleaned_texts.append(cleaned_text if cleaned_text else " ")
                else:
                    cleaned_texts.append(" ")
            
            # Generate embeddings in batch (more efficient)
            embeddings = self.model.encode(cleaned_texts, convert_to_numpy=True, show_progress_bar=False)
            
            # Convert to list of lists
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            return [[0.0] * self.embedding_dimension for _ in texts]
    
    def cosine_similarity(self, embedding1: Union[List[float], np.ndarray], 
                         embedding2: Union[List[float], np.ndarray]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            float: Cosine similarity score (0 to 1, higher is more similar)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Handle zero vectors
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(vec1, vec2) / (norm1 * norm2)
            
            # Ensure result is in [0, 1] range (sometimes numerical issues can cause slight deviations)
            similarity = max(0.0, min(1.0, similarity))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model
        
        Returns:
            dict: Model information
        """
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension,
            'max_sequence_length': self.model.max_seq_length
        }
