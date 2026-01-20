"""
Holiday Planner Agents Package

Contains specialized agents:
- IntentAgent: Parse user input into structured intent
- DataAgent: Fetch relevant data from MongoDB
- PlannerAgent: Create logical itinerary using LLM
- NarratorAgent: Generate human-readable narrative
- EmbeddingService: Generate embeddings for semantic search
- QueryClassifier: Classify user queries for routing
- KnowledgeAgent: Answer travel questions using database context
- LocationResolver: Resolve location names with fuzzy matching and hierarchy
"""

from .intent_agent import IntentAgent
from .data_agent import DataAgent
from .planner_agent import PlannerAgent
from .narrator_agent import NarratorAgent
from .embedding_service import EmbeddingService
from .query_classifier import QueryClassifier
from .knowledge_agent import KnowledgeAgent
from .location_resolver import LocationResolver

__all__ = [
    'IntentAgent', 
    'DataAgent', 
    'PlannerAgent', 
    'NarratorAgent', 
    'EmbeddingService',
    'QueryClassifier',
    'KnowledgeAgent',
    'LocationResolver'
]
