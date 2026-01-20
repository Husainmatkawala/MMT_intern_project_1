import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for holiday planner service"""
    
    # MongoDB configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/travel_blog')
    
    # Azure OpenAI configuration
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
    AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
    
    # Service configuration
    PORT = int(os.getenv('HOLIDAY_PLANNER_PORT', 5005))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # LLM configuration
    TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
    MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '2000'))
    
    # Data Agent - Query Limits (configurable per collection)
    QUERY_LIMIT_HOTELS = int(os.getenv('QUERY_LIMIT_HOTELS', '10'))
    QUERY_LIMIT_RESTAURANTS = int(os.getenv('QUERY_LIMIT_RESTAURANTS', '10'))
    QUERY_LIMIT_ACTIVITIES = int(os.getenv('QUERY_LIMIT_ACTIVITIES', '15'))
    QUERY_LIMIT_PLACES = int(os.getenv('QUERY_LIMIT_PLACES', '15'))
    QUERY_LIMIT_CABS = int(os.getenv('QUERY_LIMIT_CABS', '5'))
    QUERY_LIMIT_BUSES = int(os.getenv('QUERY_LIMIT_BUSES', '5'))
    
    # Intent Agent - Default Values
    DEFAULT_DAYS = int(os.getenv('DEFAULT_DAYS', '3'))
    DEFAULT_PEOPLE = int(os.getenv('DEFAULT_PEOPLE', '2'))
    DEFAULT_PREFERENCES = os.getenv('DEFAULT_PREFERENCES', 'culture,nature').split(',')
    
    # Intent Agent - Validation Limits
    MIN_DAYS = int(os.getenv('MIN_DAYS', '1'))
    MAX_DAYS = int(os.getenv('MAX_DAYS', '30'))
    MIN_PEOPLE = int(os.getenv('MIN_PEOPLE', '1'))
    
    # Embedding Model Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
    EMBEDDING_CACHE_SIZE = int(os.getenv('EMBEDDING_CACHE_SIZE', '1000'))
    
    # Semantic Search Configuration
    SEMANTIC_TOP_K_HOTELS = int(os.getenv('SEMANTIC_TOP_K_HOTELS', '10'))
    SEMANTIC_TOP_K_RESTAURANTS = int(os.getenv('SEMANTIC_TOP_K_RESTAURANTS', '10'))
    SEMANTIC_TOP_K_ACTIVITIES = int(os.getenv('SEMANTIC_TOP_K_ACTIVITIES', '15'))
    SEMANTIC_TOP_K_PLACES = int(os.getenv('SEMANTIC_TOP_K_PLACES', '15'))
    SEMANTIC_TOP_K_CABS = int(os.getenv('SEMANTIC_TOP_K_CABS', '5'))
    SEMANTIC_TOP_K_BUSES = int(os.getenv('SEMANTIC_TOP_K_BUSES', '5'))
    
    # Feature Flags (Always enabled - no fallbacks)
    # These are kept for backward compatibility but are always True
    USE_SEMANTIC_SEARCH = True  # Always use semantic search
    USE_LLM_INTENT_EXTRACTION = True  # Always use LLM for intent extraction
    
    # Chatbot Configuration
    SESSION_TIMEOUT_HOURS = int(os.getenv('SESSION_TIMEOUT_HOURS', '2'))
    SESSION_CLEANUP_INTERVAL_MINUTES = int(os.getenv('SESSION_CLEANUP_INTERVAL_MINUTES', '10'))
    MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', '20'))
    MAX_ACTIVE_SESSIONS = int(os.getenv('MAX_ACTIVE_SESSIONS', '1000'))
    
    # Query Classification Configuration
    KNOWLEDGE_QUERY_CONFIDENCE_THRESHOLD = float(os.getenv('KNOWLEDGE_QUERY_CONFIDENCE_THRESHOLD', '0.7'))
    
    # Chat Response Configuration
    CHAT_RESPONSE_MAX_TOKENS = int(os.getenv('CHAT_RESPONSE_MAX_TOKENS', '500'))
    CHAT_TEMPERATURE = float(os.getenv('CHAT_TEMPERATURE', '0.7'))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_configs = {
            'MONGODB_URI': cls.MONGODB_URI,
            'AZURE_OPENAI_ENDPOINT': cls.AZURE_OPENAI_ENDPOINT,
            'AZURE_OPENAI_KEY': cls.AZURE_OPENAI_KEY,
        }
        
        missing = [key for key, value in required_configs.items() if not value]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
