"""
Vector Store - LanceDB integration for semantic search of historical defects
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
from src.utils.llm_client import get_llm_client
from sentence_transformers import SentenceTransformer


class DefectEmbedding(LanceModel):
    """Schema for defect embeddings in LanceDB"""
    key: str
    summary: str
    description: str
    component: str
    root_cause: str
    status: str
    resolution: str
    labels: str  # JSON string of labels
    created: str
    resolved: Optional[str] = None
    fix_commit: Optional[str] = None
    related_file: Optional[str] = None
    duplicate_to: str  # JSON string of duplicate keys
    text: str  # Combined text for embedding
    vector: Vector(384)  # all-MiniLM-L6-v2 embedding dimension


class VectorStore:
    """Manages vector database for semantic defect search"""
    
    @staticmethod
    def distance_to_similarity(distance: float) -> float:
        """
        Convert L2 distance to similarity score (0-1)
        
        Args:
            distance: L2 distance from LanceDB (0 = identical, 2 = opposite)
            
        Returns:
            Similarity score (0-1, where 1 is most similar)
        """
        return 1.0 / (1.0 + distance)
    
    @staticmethod
    def similarity_to_percentage(similarity: float) -> float:
        """
        Convert similarity score to percentage
        
        Args:
            similarity: Similarity score (0-1)
            
        Returns:
            Percentage (0-100)
        """
        return similarity * 100.0
    
    def __init__(self, db_path: str = "data/vector_db", llm_config: Dict[str, Any] = None):
        """
        Initialize vector store
        
        Args:
            db_path: Path to LanceDB database
            llm_config: Configuration for LLM client (for embeddings)
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.llm_config = llm_config or {}
        
        # Create db directory if it doesn't exist
        Path(db_path).mkdir(parents=True, exist_ok=True)
        
        # Connect to LanceDB
        self.db = lancedb.connect(db_path)
        self.table_name = "defects"
        
        # Initialize local embedding model
        self.embedding_model_path = "src/models/all-MiniLM-L6-v2"
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_path)
            self.logger.info(f"Vector Store: Local embedding model loaded from {self.embedding_model_path}")
        except Exception as e:
            self.logger.warning(f"Vector Store: Failed to load local model, will download: {str(e)}")
            # Fallback to download if local path doesn't exist
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                self.logger.info("Vector Store: Downloaded and initialized all-MiniLM-L6-v2 model")
            except Exception as e2:
                self.logger.error(f"Vector Store: Failed to initialize embedding model: {str(e2)}")
                self.embedding_model = None
        
        # Initialize LLM client for embeddings (kept for backward compatibility)
        try:
            self.llm_client = get_llm_client(llm_config)
            self.logger.info("Vector Store: LLM client initialized for embeddings")
        except Exception as e:
            self.logger.error(f"Vector Store: Failed to initialize LLM client: {str(e)}")
            self.llm_client = None
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using local sentence-transformers model
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        if not self.embedding_model:
            raise ValueError("Embedding model not initialized. Cannot generate embeddings.")
        
        try:
            # Truncate text if too long (model typically handles ~512 tokens)
            # all-MiniLM-L6-v2 has max sequence length of 256 word pieces
            if len(text) > 8000:
                text = text[:8000]
            
            # Generate embedding using local model
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            
            # Convert to list and ensure it's the right format
            embedding_list = embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
            
            # Note: all-MiniLM-L6-v2 produces 384-dimensional embeddings
            # If you need 1536 dimensions, you'll need to update the DefectEmbedding schema
            # or use a different model like text-embedding-ada-002
            
            return embedding_list
            
        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def load_defects_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        """
        Load defects from JSON file
        
        Args:
            json_path: Path to defects JSON file
            
        Returns:
            List of defect dictionaries
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                defects = json.load(f)
            self.logger.info(f"Loaded {len(defects)} defects from {json_path}")
            return defects
        except Exception as e:
            self.logger.error(f"Error loading defects from JSON: {str(e)}")
            raise
    
    def prepare_defect_for_embedding(self, defect: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare defect data for embedding generation
        
        Args:
            defect: Defect dictionary
            
        Returns:
            Prepared defect with combined text and embedding
        """
        # Combine relevant fields into text for embedding
        text_parts = [
            f"Summary: {defect.get('summary', '')}",
            f"Description: {defect.get('description', '')}",
            f"Component: {defect.get('component', '')}",
            f"Root Cause: {defect.get('root_cause', '')}",
            f"Labels: {', '.join(defect.get('labels', []))}",
        ]
        
        combined_text = " | ".join(text_parts)
        
        # Generate embedding
        embedding = self.generate_embedding(combined_text)
        
        # Prepare data for LanceDB
        prepared = {
            "key": defect.get("key", ""),
            "summary": defect.get("summary", ""),
            "description": defect.get("description", ""),
            "component": defect.get("component", ""),
            "root_cause": defect.get("root_cause", ""),
            "status": defect.get("status", ""),
            "resolution": defect.get("resolution", ""),
            "labels": json.dumps(defect.get("labels", [])),
            "created": defect.get("created", ""),
            "resolved": defect.get("resolved"),
            "fix_commit": defect.get("fix_commit"),
            "related_file": defect.get("related_file"),
            "duplicate_to": json.dumps(defect.get("duplicate_to", [])),
            "text": combined_text,
            "vector": embedding
        }
        
        return prepared
    
    def index_defects(self, json_path: str, batch_size: int = 10):
        """
        Index defects from JSON file into vector database
        
        Args:
            json_path: Path to defects JSON file
            batch_size: Number of defects to process in each batch
        """
        self.logger.info(f"Starting to index defects from {json_path}")
        
        # Load defects
        defects = self.load_defects_from_json(json_path)
        
        # Prepare defects with embeddings
        prepared_defects = []
        total = len(defects)
        
        for i, defect in enumerate(defects):
            try:
                self.logger.info(f"Processing defect {i+1}/{total}: {defect.get('key')}")
                prepared = self.prepare_defect_for_embedding(defect)
                prepared_defects.append(prepared)
                
                # Batch insert
                if len(prepared_defects) >= batch_size:
                    self._insert_batch(prepared_defects)
                    prepared_defects = []
                    
            except Exception as e:
                self.logger.error(f"Error processing defect {defect.get('key')}: {str(e)}")
        
        # Insert remaining defects
        if prepared_defects:
            self._insert_batch(prepared_defects)
        
        self.logger.info(f"Successfully indexed {total} defects")
    
    def _insert_batch(self, defects: List[Dict[str, Any]]):
        """
        Insert a batch of defects into LanceDB
        
        Args:
            defects: List of prepared defect dictionaries
        """
        try:
            if self.table_name in self.db.table_names():
                table = self.db.open_table(self.table_name)
                table.add(defects)
            else:
                # Create new table
                table = self.db.create_table(self.table_name, data=defects)
            
            self.logger.info(f"Inserted batch of {len(defects)} defects")
        except Exception as e:
            self.logger.error(f"Error inserting batch: {str(e)}")
            raise
    
    def search_similar_defects(
        self,
        query: str,
        limit: int = 5,
        component_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar defects using semantic similarity
        
        Args:
            query: Search query (defect description or symptoms)
            limit: Maximum number of results to return
            component_filter: Optional component name to filter by
            
        Returns:
            List of similar defects with similarity scores
        """
        try:
            # Check if table exists
            if self.table_name not in self.db.table_names():
                self.logger.warning("Defects table not found. Please index defects first.")
                return []
            
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            
            # Open table
            table = self.db.open_table(self.table_name)
            
            # Perform vector search
            results = table.search(query_embedding).limit(limit)
            
            # Apply component filter if specified
            if component_filter:
                results = results.where(f"component = '{component_filter}'")
            
            # Execute search
            results_df = results.to_pandas()
            
            # Convert to list of dictionaries
            similar_defects = []
            for _, row in results_df.iterrows():
                # Get distance from LanceDB (L2 distance)
                distance = row.get("_distance", 0)
                
                # Convert distance to similarity score (0-1 scale)
                # For L2 distance with normalized embeddings:
                # - distance ranges from 0 (identical) to 2 (opposite)
                # - similarity = 1 / (1 + distance)
                # This gives: distance 0 -> similarity 1.0, distance 2 -> similarity 0.33
                similarity_score = 1.0 / (1.0 + distance)
                
                defect = {
                    "key": row["key"],
                    "summary": row["summary"],
                    "description": row["description"],
                    "component": row["component"],
                    "root_cause": row["root_cause"],
                    "status": row["status"],
                    "resolution": row["resolution"],
                    "labels": json.loads(row["labels"]),
                    "created": row["created"],
                    "resolved": row.get("resolved"),
                    "fix_commit": row.get("fix_commit"),
                    "related_file": row.get("related_file"),
                    "duplicate_to": json.loads(row["duplicate_to"]),
                    "distance": distance,  # Raw L2 distance (lower = more similar)
                    "similarity_score": similarity_score  # Normalized 0-1 score (higher = more similar)
                }
                similar_defects.append(defect)
            
            self.logger.info(f"Found {len(similar_defects)} similar defects")
            if similar_defects:
                self.logger.info(f"Top match: {similar_defects[0]['key']} "
                               f"(similarity: {similar_defects[0]['similarity_score']:.2%}, "
                               f"distance: {similar_defects[0]['distance']:.4f})")
            return similar_defects
            
        except Exception as e:
            self.logger.error(f"Error searching for similar defects: {str(e)}")
            return []
    
    def get_defect_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific defect by its key
        
        Args:
            key: Defect key (e.g., "SAM1-342")
            
        Returns:
            Defect dictionary or None if not found
        """
        try:
            if self.table_name not in self.db.table_names():
                return None
            
            table = self.db.open_table(self.table_name)
            results = table.search().where(f"key = '{key}'").limit(1).to_pandas()
            
            if len(results) == 0:
                return None
            
            row = results.iloc[0]
            return {
                "key": row["key"],
                "summary": row["summary"],
                "description": row["description"],
                "component": row["component"],
                "root_cause": row["root_cause"],
                "status": row["status"],
                "resolution": row["resolution"],
                "labels": json.loads(row["labels"]),
                "created": row["created"],
                "resolved": row.get("resolved"),
                "fix_commit": row.get("fix_commit"),
                "related_file": row.get("related_file"),
                "duplicate_to": json.loads(row["duplicate_to"])
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving defect {key}: {str(e)}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database
        
        Returns:
            Dictionary with database statistics
        """
        try:
            if self.table_name not in self.db.table_names():
                return {"total_defects": 0, "indexed": False}
            
            table = self.db.open_table(self.table_name)
            count = len(table.to_pandas())
            
            # Get component distribution
            df = table.to_pandas()
            components = df["component"].value_counts().to_dict()
            
            return {
                "total_defects": count,
                "indexed": True,
                "components": components,
                "table_name": self.table_name
            }
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return {"error": str(e)}


# Singleton instance
_vector_store_instance = None


def get_vector_store(db_path: str = "data/vector_db", llm_config: Dict[str, Any] = None) -> VectorStore:
    """
    Get or create vector store singleton
    
    Args:
        db_path: Path to LanceDB database
        llm_config: Configuration for LLM client
        
    Returns:
        VectorStore instance
    """
    global _vector_store_instance
    
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(db_path, llm_config)
    
    return _vector_store_instance


def reset_vector_store():
    """Reset the vector store singleton (useful for testing)"""
    global _vector_store_instance
    _vector_store_instance = None
