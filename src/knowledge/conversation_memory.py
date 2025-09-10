"""
LocalMind Conversation Memory System

Manages conversation history and context using vector database for intelligent memory.
Enables learning from user interactions and maintaining conversation context.
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ConversationTurn:
    """Represents a single conversation turn."""
    timestamp: str
    user_message: str
    assistant_response: str
    domain: str
    confidence: str
    context_used: List[str] = None
    
    def __post_init__(self):
        if self.context_used is None:
            self.context_used = []

@dataclass
class UserProfile:
    """Represents user preferences and learning patterns."""
    preferred_domains: List[str] = None
    common_topics: List[str] = None
    interaction_patterns: Dict[str, Any] = None
    learning_preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferred_domains is None:
            self.preferred_domains = []
        if self.common_topics is None:
            self.common_topics = []
        if self.interaction_patterns is None:
            self.interaction_patterns = {}
        if self.learning_preferences is None:
            self.learning_preferences = {}

class ConversationMemory:
    """
    Manages conversation memory and user learning.
    
    Features:
    - Conversation history storage and retrieval
    - Context-aware responses using past interactions
    - User pattern learning and adaptation
    - Semantic search through conversation history
    """
    
    def __init__(self, config: Dict[str, Any], vector_db=None):
        self.config = config
        self.vector_db = vector_db
        self.logger = logging.getLogger(__name__)
        
        # Memory configuration
        self.memory_dir = Path("data/user/memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_conversation_history = config.get('memory', {}).get('max_history', 100)
        self.context_window_size = config.get('memory', {}).get('context_window', 5)
        
        # Initialize conversation storage
        self.conversation_history: List[ConversationTurn] = []
        self.current_session_context: List[str] = []
        self.user_profile = UserProfile()
        
        # Load existing memory
        self._load_conversation_history()
        self._load_user_profile()
        
        self.logger.info("Conversation memory initialized")
    
    def add_conversation_turn(self, user_message: str, assistant_response: str, 
                            domain: str, confidence: str, context_used: List[str] = None):
        """Add a new conversation turn to memory."""
        try:
            turn = ConversationTurn(
                timestamp=datetime.now().isoformat(),
                user_message=user_message,
                assistant_response=assistant_response,
                domain=domain,
                confidence=confidence,
                context_used=context_used or []
            )
            
            self.conversation_history.append(turn)
            
            # Maintain memory size limits
            if len(self.conversation_history) > self.max_conversation_history:
                self.conversation_history = self.conversation_history[-self.max_conversation_history:]
            
            # Update current session context
            self.current_session_context.append(user_message)
            if len(self.current_session_context) > self.context_window_size:
                self.current_session_context = self.current_session_context[-self.context_window_size:]
            
            # Store in vector database for semantic search
            if self.vector_db:
                self._add_to_vector_memory(turn)
            
            # Update user profile
            self._update_user_profile(turn)
            
            # Save to disk
            self._save_conversation_history()
            self._save_user_profile()
            
            self.logger.debug(f"Added conversation turn to memory")
            
        except Exception as e:
            self.logger.error(f"Failed to add conversation turn: {e}")
    
    def get_relevant_context(self, current_message: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Get relevant conversation context for the current message."""
        context = []
        
        try:
            # Get recent conversation context
            recent_context = self._get_recent_context()
            context.extend(recent_context)
            
            # Get semantically similar past conversations
            if self.vector_db:
                similar_context = self._get_similar_conversations(current_message, max_results)
                context.extend(similar_context)
            
            # Get user pattern context
            pattern_context = self._get_pattern_context(current_message)
            context.extend(pattern_context)
            
            return context[:max_results * 2]  # Limit total context
            
        except Exception as e:
            self.logger.error(f"Failed to get relevant context: {e}")
            return []
    
    def _get_recent_context(self) -> List[Dict[str, Any]]:
        """Get recent conversation turns for context."""
        context = []
        
        # Get last few turns from current session
        recent_turns = self.conversation_history[-self.context_window_size:]
        
        for turn in recent_turns:
            context.append({
                'type': 'recent_conversation',
                'content': f"User: {turn.user_message}\nAssistant: {turn.assistant_response}",
                'timestamp': turn.timestamp,
                'domain': turn.domain,
                'relevance': 'high'
            })
        
        return context
    
    def _get_similar_conversations(self, current_message: str, max_results: int) -> List[Dict[str, Any]]:
        """Get semantically similar past conversations."""
        context = []
        
        try:
            # Search for similar conversations in vector database
            results = self.vector_db.search_by_domain(
                query=current_message,
                domain='conversation_memory',
                k=max_results
            )
            
            for result in results:
                if result['score'] > 0.7:  # Only high similarity
                    context.append({
                        'type': 'similar_conversation',
                        'content': result['content'],
                        'timestamp': result.get('timestamp', ''),
                        'relevance': 'medium',
                        'similarity_score': result['score']
                    })
        
        except Exception as e:
            self.logger.error(f"Failed to get similar conversations: {e}")
        
        return context
    
    def _get_pattern_context(self, current_message: str) -> List[Dict[str, Any]]:
        """Get context based on user patterns and preferences."""
        context = []
        
        try:
            # Analyze message for topics
            message_lower = current_message.lower()
            
            # Check for user's preferred topics
            for topic in self.user_profile.common_topics:
                if topic.lower() in message_lower:
                    context.append({
                        'type': 'user_preference',
                        'content': f"User frequently asks about: {topic}",
                        'relevance': 'medium'
                    })
            
            # Check for preferred domains
            for domain in self.user_profile.preferred_domains:
                context.append({
                    'type': 'domain_preference',
                    'content': f"User prefers {domain} domain responses",
                    'relevance': 'low'
                })
        
        except Exception as e:
            self.logger.error(f"Failed to get pattern context: {e}")
        
        return context
    
    def _add_to_vector_memory(self, turn: ConversationTurn):
        """Add conversation turn to vector database for semantic search."""
        try:
            # Create searchable content
            content = f"User: {turn.user_message}\nAssistant: {turn.assistant_response}"
            
            # Create metadata
            metadata = {
                'type': 'conversation_turn',
                'timestamp': turn.timestamp,
                'domain': turn.domain,
                'confidence': turn.confidence,
                'user_message': turn.user_message,
                'assistant_response': turn.assistant_response
            }
            
            # Add to vector database
            self.vector_db.add_document(
                content=content,
                domain='conversation_memory',
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to add to vector memory: {e}")
    
    def _update_user_profile(self, turn: ConversationTurn):
        """Update user profile based on conversation turn."""
        try:
            # Update preferred domains
            if turn.domain not in self.user_profile.preferred_domains:
                self.user_profile.preferred_domains.append(turn.domain)
            
            # Extract and update common topics (simple keyword extraction)
            keywords = self._extract_keywords(turn.user_message)
            for keyword in keywords:
                if keyword not in self.user_profile.common_topics:
                    self.user_profile.common_topics.append(keyword)
            
            # Limit list sizes
            self.user_profile.preferred_domains = self.user_profile.preferred_domains[-10:]
            self.user_profile.common_topics = self.user_profile.common_topics[-20:]
            
        except Exception as e:
            self.logger.error(f"Failed to update user profile: {e}")
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction from text."""
        # Remove common words and extract meaningful terms
        common_words = {
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'to', 'are', 'as', 'was', 'were',
            'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'what', 'who', 'where', 'when', 'why', 'how',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        words = text.lower().split()
        keywords = [word.strip('.,!?;:') for word in words 
                   if len(word) > 3 and word.lower() not in common_words]
        
        return list(set(keywords))[:10]  # Return unique keywords, max 10
    
    def _load_conversation_history(self):
        """Load conversation history from disk."""
        try:
            history_file = self.memory_dir / "conversation_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.conversation_history = [
                        ConversationTurn(**turn_data) for turn_data in data
                    ]
                self.logger.info(f"Loaded {len(self.conversation_history)} conversation turns")
        except Exception as e:
            self.logger.error(f"Failed to load conversation history: {e}")
    
    def _save_conversation_history(self):
        """Save conversation history to disk."""
        try:
            history_file = self.memory_dir / "conversation_history.json"
            data = [
                {
                    'timestamp': turn.timestamp,
                    'user_message': turn.user_message,
                    'assistant_response': turn.assistant_response,
                    'domain': turn.domain,
                    'confidence': turn.confidence,
                    'context_used': turn.context_used
                }
                for turn in self.conversation_history
            ]
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save conversation history: {e}")
    
    def _load_user_profile(self):
        """Load user profile from disk."""
        try:
            profile_file = self.memory_dir / "user_profile.json"
            if profile_file.exists():
                with open(profile_file, 'r') as f:
                    data = json.load(f)
                    self.user_profile = UserProfile(**data)
                self.logger.info("Loaded user profile")
        except Exception as e:
            self.logger.error(f"Failed to load user profile: {e}")
    
    def _save_user_profile(self):
        """Save user profile to disk."""
        try:
            profile_file = self.memory_dir / "user_profile.json"
            data = {
                'preferred_domains': self.user_profile.preferred_domains,
                'common_topics': self.user_profile.common_topics,
                'interaction_patterns': self.user_profile.interaction_patterns,
                'learning_preferences': self.user_profile.learning_preferences
            }
            with open(profile_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save user profile: {e}")
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about conversations."""
        return {
            'total_conversations': len(self.conversation_history),
            'current_session_length': len(self.current_session_context),
            'preferred_domains': self.user_profile.preferred_domains,
            'common_topics': self.user_profile.common_topics[:10],  # Top 10
            'memory_usage': f"{len(self.conversation_history)}/{self.max_conversation_history}"
        }
