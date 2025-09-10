"""
LocalMind Offline Learning System

Implements safe offline learning mechanism that improves model performance
from user interactions while maintaining privacy and security.
"""

import logging
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class LearningFeedback:
    """Structure for learning feedback."""
    query: str
    response: str
    feedback_type: str  # positive, negative, correction
    feedback_value: Optional[str] = None  # correction text if applicable
    domain: Optional[str] = None
    timestamp: str = None
    session_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class OfflineLearner:
    """
    Offline learning system for LocalMind.
    
    Features:
    - Safe learning from user feedback
    - Privacy-preserving data collection
    - Content filtering and validation
    - Incremental knowledge base updates
    """
    
    def __init__(self, config: Dict[str, Any], vector_db=None):
        self.config = config
        self.vector_db = vector_db
        self.logger = logging.getLogger(__name__)
        
        # Learning configuration
        self.learning_enabled = config['knowledge']['learning']['enabled']
        self.safety_filter = config['knowledge']['learning']['safety_filter']
        self.max_feedback_per_session = config['knowledge']['learning']['max_feedback_per_session']
        self.learning_rate = config['knowledge']['learning']['learning_rate']
        
        # Storage paths
        self.learning_dir = Path("data/user/learning")
        self.learning_dir.mkdir(parents=True, exist_ok=True)
        
        # Session tracking
        self.session_feedback_count = 0
        self.session_id = self._generate_session_id()
        
        # Feedback storage
        self.feedback_queue = []
        self.processed_feedback = []
        
        self.logger.info(f"OfflineLearner initialized (enabled: {self.learning_enabled})")
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def add_feedback(self, query: str, response: str, feedback_type: str, 
                    feedback_value: Optional[str] = None, domain: Optional[str] = None) -> bool:
        """
        Add user feedback for learning.
        
        Args:
            query: Original user query
            response: Model response
            feedback_type: Type of feedback (positive, negative, correction)
            feedback_value: Additional feedback data (e.g., correction)
            domain: Domain context
            
        Returns:
            Success status
        """
        if not self.learning_enabled:
            self.logger.debug("Learning disabled, ignoring feedback")
            return False
        
        try:
            # Check session limits
            if self.session_feedback_count >= self.max_feedback_per_session:
                self.logger.warning("Session feedback limit reached")
                return False
            
            # Create feedback object
            feedback = LearningFeedback(
                query=query,
                response=response,
                feedback_type=feedback_type,
                feedback_value=feedback_value,
                domain=domain,
                session_id=self.session_id
            )
            
            # Apply safety filtering
            if self.safety_filter and not self._is_safe_feedback(feedback):
                self.logger.warning("Feedback filtered by safety check")
                return False
            
            # Add to queue
            self.feedback_queue.append(feedback)
            self.session_feedback_count += 1
            
            self.logger.info(f"Feedback added: {feedback_type}")
            
            # Process feedback if queue is full
            if len(self.feedback_queue) >= 5:  # Process in batches
                self.process_feedback_queue()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add feedback: {e}")
            return False
    
    def _is_safe_feedback(self, feedback: LearningFeedback) -> bool:
        """Check if feedback is safe for learning."""
        try:
            # Content safety checks
            unsafe_patterns = [
                'password', 'credit card', 'ssn', 'social security',
                'personal information', 'private', 'confidential'
            ]
            
            content_to_check = f"{feedback.query} {feedback.response}"
            if feedback.feedback_value:
                content_to_check += f" {feedback.feedback_value}"
            
            content_lower = content_to_check.lower()
            
            # Check for unsafe patterns
            for pattern in unsafe_patterns:
                if pattern in content_lower:
                    return False
            
            # Length checks
            if len(feedback.query) > 1000 or len(feedback.response) > 2000:
                return False
            
            # Domain validation
            valid_domains = ['education', 'healthcare', 'general']
            if feedback.domain and feedback.domain not in valid_domains:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Safety check failed: {e}")
            return False
    
    def process_feedback_queue(self):
        """Process queued feedback for learning."""
        if not self.feedback_queue:
            return
        
        try:
            self.logger.info(f"Processing {len(self.feedback_queue)} feedback items")
            
            for feedback in self.feedback_queue:
                self._process_single_feedback(feedback)
            
            # Save processed feedback
            self._save_feedback_batch(self.feedback_queue)
            
            # Clear queue
            self.processed_feedback.extend(self.feedback_queue)
            self.feedback_queue.clear()
            
            self.logger.info("Feedback processing completed")
            
        except Exception as e:
            self.logger.error(f"Feedback processing failed: {e}")
    
    def _process_single_feedback(self, feedback: LearningFeedback):
        """Process a single feedback item."""
        try:
            if feedback.feedback_type == 'positive':
                self._handle_positive_feedback(feedback)
            elif feedback.feedback_type == 'negative':
                self._handle_negative_feedback(feedback)
            elif feedback.feedback_type == 'correction':
                self._handle_correction_feedback(feedback)
            
        except Exception as e:
            self.logger.error(f"Failed to process feedback: {e}")
    
    def _handle_positive_feedback(self, feedback: LearningFeedback):
        """Handle positive feedback to reinforce good responses."""
        # For positive feedback, we can increase the weight/importance
        # of the query-response pair in future retrievals
        
        if self.vector_db:
            # Add successful query-response pair to knowledge base
            enhanced_content = f"Q: {feedback.query}\nA: {feedback.response}"
            metadata = {
                "id": f"learned_{feedback.session_id}_{datetime.now().timestamp()}",
                "domain": feedback.domain or "general",
                "type": "user_validated",
                "feedback_type": "positive",
                "timestamp": feedback.timestamp,
                "source": "user_feedback"
            }
            
            self.vector_db.add_documents([enhanced_content], [metadata])
            self.logger.debug("Positive feedback added to knowledge base")
    
    def _handle_negative_feedback(self, feedback: LearningFeedback):
        """Handle negative feedback to avoid similar responses."""
        # For negative feedback, we log the problematic pattern
        # This could be used to modify future responses
        
        negative_log = {
            "query_pattern": self._extract_query_pattern(feedback.query),
            "response_pattern": self._extract_response_pattern(feedback.response),
            "domain": feedback.domain,
            "timestamp": feedback.timestamp
        }
        
        self._save_negative_pattern(negative_log)
        self.logger.debug("Negative feedback pattern logged")
    
    def _handle_correction_feedback(self, feedback: LearningFeedback):
        """Handle correction feedback to learn better responses."""
        if not feedback.feedback_value:
            return
        
        # Add corrected response to knowledge base
        if self.vector_db:
            corrected_content = f"Q: {feedback.query}\nA: {feedback.feedback_value}"
            metadata = {
                "id": f"corrected_{feedback.session_id}_{datetime.now().timestamp()}",
                "domain": feedback.domain or "general",
                "type": "user_corrected",
                "feedback_type": "correction",
                "original_response": feedback.response,
                "timestamp": feedback.timestamp,
                "source": "user_correction"
            }
            
            self.vector_db.add_documents([corrected_content], [metadata])
            self.logger.debug("Correction added to knowledge base")
    
    def _extract_query_pattern(self, query: str) -> str:
        """Extract pattern from query for learning."""
        # Simple pattern extraction - could be enhanced
        words = query.lower().split()
        # Remove common words and keep content words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        content_words = [w for w in words if w not in stopwords and len(w) > 2]
        return ' '.join(content_words[:5])  # First 5 content words
    
    def _extract_response_pattern(self, response: str) -> str:
        """Extract pattern from response for learning."""
        # Simple response pattern - first sentence or first 100 chars
        if '.' in response:
            first_sentence = response.split('.')[0]
            return first_sentence[:100]
        else:
            return response[:100]
    
    def _save_feedback_batch(self, feedback_batch: List[LearningFeedback]):
        """Save processed feedback to disk."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.learning_dir / f"feedback_batch_{timestamp}.json"
            
            # Convert to serializable format
            serializable_batch = [asdict(fb) for fb in feedback_batch]
            
            with open(filename, 'w') as f:
                json.dump(serializable_batch, f, indent=2)
            
            self.logger.debug(f"Feedback batch saved to {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save feedback batch: {e}")
    
    def _save_negative_pattern(self, pattern: Dict[str, Any]):
        """Save negative feedback pattern."""
        try:
            patterns_file = self.learning_dir / "negative_patterns.jsonl"
            
            with open(patterns_file, 'a') as f:
                f.write(json.dumps(pattern) + '\n')
            
        except Exception as e:
            self.logger.error(f"Failed to save negative pattern: {e}")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning system statistics."""
        return {
            "learning_enabled": self.learning_enabled,
            "session_id": self.session_id,
            "session_feedback_count": self.session_feedback_count,
            "queue_size": len(self.feedback_queue),
            "total_processed": len(self.processed_feedback),
            "max_feedback_per_session": self.max_feedback_per_session
        }
    
    def load_historical_feedback(self) -> List[Dict[str, Any]]:
        """Load historical feedback for analysis."""
        try:
            feedback_files = list(self.learning_dir.glob("feedback_batch_*.json"))
            all_feedback = []
            
            for file_path in feedback_files:
                with open(file_path, 'r') as f:
                    batch = json.load(f)
                    all_feedback.extend(batch)
            
            return all_feedback
            
        except Exception as e:
            self.logger.error(f"Failed to load historical feedback: {e}")
            return []
    
    def cleanup_old_feedback(self, days_to_keep: int = 30):
        """Clean up old feedback files."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            feedback_files = list(self.learning_dir.glob("feedback_batch_*.json"))
            
            for file_path in feedback_files:
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    file_path.unlink()
                    self.logger.debug(f"Deleted old feedback file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old feedback: {e}")
    
    def export_learned_knowledge(self) -> Dict[str, List[str]]:
        """Export learned knowledge for review."""
        try:
            if not self.vector_db:
                return {}
            
            # Get all learned content from vector database
            # This would require additional methods in VectorDatabase
            # For now, return summary from processed feedback
            
            feedback_data = self.load_historical_feedback()
            
            learned_content = {
                "positive_examples": [],
                "corrections": [],
                "patterns": []
            }
            
            for feedback in feedback_data:
                if feedback.get('feedback_type') == 'positive':
                    learned_content["positive_examples"].append(
                        f"Q: {feedback['query']} A: {feedback['response']}"
                    )
                elif feedback.get('feedback_type') == 'correction':
                    learned_content["corrections"].append(
                        f"Q: {feedback['query']} Original: {feedback['response']} "
                        f"Corrected: {feedback.get('feedback_value', '')}"
                    )
            
            return learned_content
            
        except Exception as e:
            self.logger.error(f"Failed to export learned knowledge: {e}")
            return {}
    
    def reset_session(self):
        """Reset current learning session."""
        self.session_id = self._generate_session_id()
        self.session_feedback_count = 0
        self.feedback_queue.clear()
        self.logger.info("Learning session reset")
