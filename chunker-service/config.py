import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for chunker service"""
    
    # MongoDB configuration
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/travel_blog')
    
    # Azure OpenAI configuration
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
    AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
    
    # Service configuration
    PORT = int(os.getenv('CHUNKER_SERVICE_PORT', 5004))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
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
