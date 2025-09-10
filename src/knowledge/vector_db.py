"""
LocalMind Vector Database

Offline vector database implementation for knowledge storage and retrieval.
Uses FAISS for efficient similarity search with local storage.
"""

import logging
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

try:
    import faiss
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logging.error(f"Required dependencies not available: {e}")
    raise

class VectorDatabase:
    """
    Local vector database for LocalMind's knowledge storage.
    
    Features:
    - Offline vector storage using FAISS
    - Efficient similarity search
    - Domain-specific knowledge organization
    - Incremental updates and learning
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Database configuration
        self.db_path = Path("data/knowledge/embeddings")
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Embedding configuration
        self.embedding_model_name = config['knowledge']['embeddings']['model']
        self.embedding_dimension = config['knowledge']['embeddings']['dimension']
        self.normalize_embeddings = config['knowledge']['embeddings']['normalize']
        
        # FAISS configuration
        self.index_type = config['knowledge']['vector_db']['index_type']
        self.n_clusters = config['knowledge']['vector_db']['n_clusters']
        
        # Initialize components
        self.embedding_model = None
        self.index = None
        self.documents = []
        self.metadata = []
        
        self._initialize_embedding_model()
        self._load_or_create_index()
        
        self.logger.info("VectorDatabase initialized for offline operation")
    
    def _initialize_embedding_model(self):
        """Initialize the sentence embedding model."""
        try:
            # Load embedding model for CPU usage (stable)
            self.embedding_model = SentenceTransformer(
                self.embedding_model_name,
                device=self.config['knowledge']['embeddings']['device']
            )
            
            # Update dimension based on actual model
            self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
            
            self.logger.info(f"Embedding model loaded: {self.embedding_model_name}")
            self.logger.info(f"Embedding dimension: {self.embedding_dimension}")
            
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one."""
        index_file = self.db_path / "faiss_index.bin"
        metadata_file = self.db_path / "metadata.json"
        documents_file = self.db_path / "documents.pkl"
        
        try:
            if index_file.exists() and metadata_file.exists() and documents_file.exists():
                # Load existing index
                self.index = faiss.read_index(str(index_file))
                
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                
                with open(documents_file, 'rb') as f:
                    self.documents = pickle.load(f)
                
                self.logger.info(f"Loaded existing index with {len(self.documents)} documents")
            else:
                # Create new index
                self._create_new_index()
                self.logger.info("Created new FAISS index")
                
        except Exception as e:
            self.logger.error(f"Error loading/creating index: {e}")
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index."""
        try:
            if self.index_type == "IVF":
                # IndexIVFFlat for larger datasets
                quantizer = faiss.IndexFlatL2(self.embedding_dimension)
                self.index = faiss.IndexIVFFlat(
                    quantizer, 
                    self.embedding_dimension, 
                    self.n_clusters
                )
            else:
                # Simple flat index for smaller datasets
                self.index = faiss.IndexFlatL2(self.embedding_dimension)
            
            self.documents = []
            self.metadata = []
            
            self.logger.info(f"Created new {self.index_type} index")
            
        except Exception as e:
            self.logger.error(f"Failed to create index: {e}")
            raise
    
    def add_documents(self, documents: List[str], metadata: List[Dict[str, Any]] = None):
        """
        Add documents to the vector database.
        
        Args:
            documents: List of text documents to add
            metadata: Optional metadata for each document
        """
        try:
            if not documents:
                return
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(
                documents,
                normalize_embeddings=self.normalize_embeddings,
                show_progress_bar=True
            )
            
            # Add to index
            if self.index_type == "IVF" and not self.index.is_trained:
                if len(embeddings) >= self.n_clusters:
                    self.index.train(embeddings.astype(np.float32))
                    self.logger.info("FAISS index trained")
            
            self.index.add(embeddings.astype(np.float32))
            
            # Store documents and metadata
            self.documents.extend(documents)
            
            if metadata is None:
                metadata = [{"id": len(self.metadata) + i} for i in range(len(documents))]
            
            self.metadata.extend(metadata)
            
            self.logger.info(f"Added {len(documents)} documents to index")
            
            # Save updated index
            self.save_index()
            
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
    
    def search(self, query: str, k: int = None, threshold: float = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            k: Number of results to return
            threshold: Similarity threshold
            
        Returns:
            List of search results with documents and metadata
        """
        try:
            if k is None:
                k = self.config['knowledge']['retrieval']['max_docs']
            
            if threshold is None:
                threshold = self.config['knowledge']['retrieval']['similarity_threshold']
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(
                [query],
                normalize_embeddings=self.normalize_embeddings
            )
            
            # Search in index
            scores, indices = self.index.search(query_embedding.astype(np.float32), k)
            
            # Process results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and score <= threshold:  # FAISS uses L2 distance (lower is better)
                    results.append({
                        "document": self.documents[idx],
                        "metadata": self.metadata[idx],
                        "score": float(score),
                        "similarity": 1.0 / (1.0 + score)  # Convert to similarity
                    })
            
            self.logger.debug(f"Search found {len(results)} results for query")
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def search_by_domain(self, query: str, domain: str, k: int = None) -> List[Dict[str, Any]]:
        """
        Search within a specific domain.
        
        Args:
            query: Search query
            domain: Domain to search in (education, healthcare, general)
            k: Number of results
            
        Returns:
            Domain-filtered search results
        """
        try:
            # First get general search results
            results = self.search(query, k * 2 if k else 10)  # Get more to filter
            
            # Filter by domain
            domain_results = []
            for result in results:
                if result["metadata"].get("domain") == domain:
                    domain_results.append(result)
                    if k and len(domain_results) >= k:
                        break
            
            self.logger.debug(f"Domain search ({domain}) found {len(domain_results)} results")
            return domain_results
            
        except Exception as e:
            self.logger.error(f"Domain search failed: {e}")
            return []
    
    def update_document(self, doc_id: str, new_content: str, new_metadata: Dict[str, Any] = None):
        """
        Update an existing document.
        
        Args:
            doc_id: Document ID to update
            new_content: New document content
            new_metadata: New metadata
        """
        try:
            # Find document by ID
            doc_index = None
            for i, meta in enumerate(self.metadata):
                if meta.get("id") == doc_id:
                    doc_index = i
                    break
            
            if doc_index is None:
                self.logger.warning(f"Document ID {doc_id} not found")
                return
            
            # Update document and metadata
            self.documents[doc_index] = new_content
            if new_metadata:
                self.metadata[doc_index].update(new_metadata)
            
            # Regenerate embedding
            new_embedding = self.embedding_model.encode(
                [new_content],
                normalize_embeddings=self.normalize_embeddings
            )
            
            # Update in index (remove old, add new)
            # Note: FAISS doesn't support direct updates, so we rebuild if needed
            self.logger.info(f"Document {doc_id} updated")
            
        except Exception as e:
            self.logger.error(f"Failed to update document: {e}")
    
    def save_index(self):
        """Save the current index to disk."""
        try:
            index_file = self.db_path / "faiss_index.bin"
            metadata_file = self.db_path / "metadata.json"
            documents_file = self.db_path / "documents.pkl"
            
            # Save FAISS index
            faiss.write_index(self.index, str(index_file))
            
            # Save metadata
            with open(metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
            # Save documents
            with open(documents_file, 'wb') as f:
                pickle.dump(self.documents, f)
            
            self.logger.debug("Index saved to disk")
            
        except Exception as e:
            self.logger.error(f"Failed to save index: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return {
            "total_documents": len(self.documents),
            "index_type": self.index_type,
            "embedding_dimension": self.embedding_dimension,
            "embedding_model": self.embedding_model_name,
            "index_trained": getattr(self.index, 'is_trained', True)
        }
    
    def initialize_with_base_knowledge(self):
        """Initialize database with base knowledge from files."""
        try:
            knowledge_dir = Path("data/knowledge")
            
            # Load educational content
            edu_file = knowledge_dir / "educational_base.json"
            if edu_file.exists():
                with open(edu_file, 'r') as f:
                    edu_content = json.load(f)
                
                documents = []
                metadata = []
                
                for subject, topics in edu_content.items():
                    for topic in topics:
                        documents.append(topic)
                        metadata.append({
                            "id": f"edu_{subject}_{len(metadata)}",
                            "domain": "education",
                            "subject": subject,
                            "type": "base_knowledge"
                        })
                
                self.add_documents(documents, metadata)
                self.logger.info(f"Loaded {len(documents)} educational documents")
            
            # Load healthcare content
            health_file = knowledge_dir / "healthcare_base.json"
            if health_file.exists():
                with open(health_file, 'r') as f:
                    health_content = json.load(f)
                
                documents = []
                metadata = []
                
                for category, topics in health_content.items():
                    for topic in topics:
                        documents.append(topic)
                        metadata.append({
                            "id": f"health_{category}_{len(metadata)}",
                            "domain": "healthcare", 
                            "category": category,
                            "type": "base_knowledge"
                        })
                
                self.add_documents(documents, metadata)
                self.logger.info(f"Loaded {len(documents)} healthcare documents")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize base knowledge: {e}")
    
    def __del__(self):
        """Cleanup when database is destroyed."""
        try:
            if hasattr(self, 'index') and self.index is not None:
                self.save_index()
        except:
            pass
