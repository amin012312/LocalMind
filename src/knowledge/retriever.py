"""
LocalMind Knowledge Retriever

Intelligent knowledge retrieval system that combines vector search with
context-aware filtering and ranking for optimal offline assistance.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class RetrievalResult:
    """Structure for retrieval results."""
    content: str
    metadata: Dict[str, Any]
    relevance_score: float
    source: str
    domain: str

class KnowledgeRetriever:
    """
    Knowledge retrieval system for LocalMind.
    
    Features:
    - Context-aware retrieval
    - Domain-specific filtering
    - Multi-stage ranking
    - Relevance scoring
    """
    
    def __init__(self, config: Dict[str, Any], vector_db=None):
        self.config = config
        self.vector_db = vector_db
        self.logger = logging.getLogger(__name__)
        
        # Retrieval configuration
        self.max_docs = config['knowledge']['retrieval']['max_docs']
        self.similarity_threshold = config['knowledge']['retrieval']['similarity_threshold']
        self.rerank = config['knowledge']['retrieval']['rerank']
        
        self.logger.info("KnowledgeRetriever initialized")
    
    def retrieve(self, query: str, domain: Optional[str] = None, 
                context: Optional[str] = None, max_results: Optional[int] = None) -> List[RetrievalResult]:
        """
        Retrieve relevant knowledge for a query.
        
        Args:
            query: User query
            domain: Specific domain to search (education, healthcare, general)
            context: Additional context for better retrieval
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant knowledge items
        """
        try:
            if max_results is None:
                max_results = self.max_docs
            
            # Enhance query with context if provided
            enhanced_query = self._enhance_query(query, context)
            
            # Perform vector search
            if domain:
                search_results = self.vector_db.search_by_domain(enhanced_query, domain, max_results * 2)
            else:
                search_results = self.vector_db.search(enhanced_query, max_results * 2)
            
            # Convert to RetrievalResult objects
            retrieval_results = []
            for result in search_results:
                retrieval_result = RetrievalResult(
                    content=result['document'],
                    metadata=result['metadata'],
                    relevance_score=result['similarity'],
                    source=result['metadata'].get('source', 'knowledge_base'),
                    domain=result['metadata'].get('domain', 'general')
                )
                retrieval_results.append(retrieval_result)
            
            # Apply additional filtering and ranking
            filtered_results = self._filter_results(retrieval_results, query, domain)
            
            # Re-rank if enabled
            if self.rerank:
                ranked_results = self._rerank_results(filtered_results, query, context)
            else:
                ranked_results = filtered_results
            
            # Return top results
            final_results = ranked_results[:max_results]
            
            self.logger.debug(f"Retrieved {len(final_results)} knowledge items for query")
            return final_results
            
        except Exception as e:
            self.logger.error(f"Knowledge retrieval failed: {e}")
            return []
    
    def _enhance_query(self, query: str, context: Optional[str] = None) -> str:
        """Enhance query with additional context."""
        if context:
            # Simple context enhancement - could be made more sophisticated
            enhanced = f"{context} {query}"
            self.logger.debug("Query enhanced with context")
            return enhanced
        return query
    
    def _filter_results(self, results: List[RetrievalResult], query: str, 
                       domain: Optional[str] = None) -> List[RetrievalResult]:
        """Apply additional filtering to search results."""
        filtered = []
        
        for result in results:
            # Relevance threshold filtering
            if result.relevance_score < self.similarity_threshold:
                continue
            
            # Domain filtering (if not already done)
            if domain and result.domain != domain:
                continue
            
            # Content quality filtering
            if not self._is_quality_content(result.content):
                continue
            
            # Query relevance check
            if self._is_relevant_to_query(result.content, query):
                filtered.append(result)
        
        return filtered
    
    def _is_quality_content(self, content: str) -> bool:
        """Check if content meets quality standards."""
        # Basic quality checks
        if len(content.strip()) < 10:  # Too short
            return False
        
        if content.count('\n') > 20:  # Too fragmented
            return False
        
        # Could add more sophisticated quality checks
        return True
    
    def _is_relevant_to_query(self, content: str, query: str) -> bool:
        """Check relevance of content to query."""
        # Simple keyword-based relevance check
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        # Check for keyword overlap
        overlap = len(query_words.intersection(content_words))
        relevance_ratio = overlap / len(query_words) if query_words else 0
        
        return relevance_ratio > 0.1  # At least 10% word overlap
    
    def _rerank_results(self, results: List[RetrievalResult], query: str, 
                       context: Optional[str] = None) -> List[RetrievalResult]:
        """Re-rank results using additional criteria."""
        try:
            # Calculate enhanced scores
            for result in results:
                enhanced_score = self._calculate_enhanced_score(result, query, context)
                result.relevance_score = enhanced_score
            
            # Sort by enhanced score
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            self.logger.debug("Results re-ranked")
            return results
            
        except Exception as e:
            self.logger.error(f"Re-ranking failed: {e}")
            return results
    
    def _calculate_enhanced_score(self, result: RetrievalResult, query: str, 
                                 context: Optional[str] = None) -> float:
        """Calculate enhanced relevance score."""
        base_score = result.relevance_score
        
        # Boost factors
        domain_boost = 1.0
        freshness_boost = 1.0
        quality_boost = 1.0
        
        # Domain-specific boosting
        if context:
            if 'education' in context.lower() and result.domain == 'education':
                domain_boost = 1.2
            elif 'health' in context.lower() and result.domain == 'healthcare':
                domain_boost = 1.2
        
        # Content quality boosting
        content_length = len(result.content)
        if 100 <= content_length <= 500:  # Optimal length
            quality_boost = 1.1
        elif content_length > 1000:  # Too long
            quality_boost = 0.9
        
        # Source reliability boosting
        source_boost = 1.0
        source = result.metadata.get('source', 'unknown')
        if source == 'verified':
            source_boost = 1.2
        elif source == 'base_knowledge':
            source_boost = 1.1
        
        # Calculate final score
        enhanced_score = base_score * domain_boost * freshness_boost * quality_boost * source_boost
        
        return min(enhanced_score, 1.0)  # Cap at 1.0
    
    def retrieve_for_domain(self, query: str, domain: str, 
                           subject: Optional[str] = None) -> List[RetrievalResult]:
        """
        Retrieve knowledge for a specific domain and subject.
        
        Args:
            query: User query
            domain: Target domain (education, healthcare)
            subject: Specific subject within domain
            
        Returns:
            Domain-specific results
        """
        try:
            # Build enhanced query for domain
            domain_query = query
            if subject:
                domain_query = f"{subject} {query}"
            
            # Perform domain-specific search
            results = self.retrieve(domain_query, domain=domain)
            
            # Further filter by subject if specified
            if subject:
                subject_results = []
                for result in results:
                    if (result.metadata.get('subject') == subject or
                        subject.lower() in result.content.lower()):
                        subject_results.append(result)
                results = subject_results
            
            self.logger.debug(f"Domain retrieval ({domain}) returned {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Domain retrieval failed: {e}")
            return []
    
    def get_related_topics(self, topic: str, domain: Optional[str] = None) -> List[str]:
        """
        Get topics related to the given topic.
        
        Args:
            topic: Main topic
            domain: Optional domain filter
            
        Returns:
            List of related topics
        """
        try:
            # Search for related content
            results = self.retrieve(topic, domain=domain, max_results=10)
            
            # Extract related topics from metadata
            related_topics = set()
            for result in results:
                # From subject/category metadata
                if 'subject' in result.metadata:
                    related_topics.add(result.metadata['subject'])
                if 'category' in result.metadata:
                    related_topics.add(result.metadata['category'])
                
                # From tags if available
                if 'tags' in result.metadata:
                    related_topics.update(result.metadata['tags'])
            
            # Remove the original topic
            related_topics.discard(topic.lower())
            
            return list(related_topics)[:5]  # Return top 5
            
        except Exception as e:
            self.logger.error(f"Failed to get related topics: {e}")
            return []
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics."""
        if self.vector_db:
            db_stats = self.vector_db.get_stats()
        else:
            db_stats = {}
        
        return {
            "database_stats": db_stats,
            "max_docs": self.max_docs,
            "similarity_threshold": self.similarity_threshold,
            "rerank_enabled": self.rerank
        }
