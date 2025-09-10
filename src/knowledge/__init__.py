"""
Knowledge Package for LocalMind

Contains vector database, retrieval system, and offline learning components.
"""

from .vector_db import VectorDatabase
from .retriever import KnowledgeRetriever  
from .updater import OfflineLearner

__all__ = ['VectorDatabase', 'KnowledgeRetriever', 'OfflineLearner']
