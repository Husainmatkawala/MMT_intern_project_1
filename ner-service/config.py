import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for NER service"""
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv('MONGODB_URI')
    
    # Server Configuration
    PORT = int(os.getenv('PORT', 5001))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # OpenAI Model Parameters
    TEMPERATURE = 0
    MAX_TOKENS = 150
    TIMEOUT = 8
    MAX_RETRIES = 0
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'AZURE_OPENAI_KEY',
            'AZURE_OPENAI_ENDPOINT',
            'MONGODB_URI'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
