import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of blog_score_Service)
project_root = Path(__file__).parent.parent

# Load backend/.env (lines 1-25 - we'll load the whole file)
backend_env_path = project_root / 'backend' / '.env'
if backend_env_path.exists():
    load_dotenv(backend_env_path, override=False)

# Load ner-service/.env (lines 1-15 - we'll load the whole file)
ner_env_path = project_root / 'ner-service' / '.env'
if ner_env_path.exists():
    load_dotenv(ner_env_path, override=False)

# Also try loading from current directory if .env exists
load_dotenv(override=False)

class Config:
    """Configuration class for Blog Score Service"""
    
    # Azure OpenAI Configuration (from ner-service/.env)
    AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
    AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2025-01-01-preview')
    
    # MongoDB Configuration (from backend/.env)
    MONGODB_URI = os.getenv('MONGODB_URI')
    
    # Server Configuration
    PORT = int(os.getenv('BLOG_SCORE_SERVICE_PORT', 5003))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # OpenAI Model Parameters
    TEMPERATURE = 0.3  # Slightly higher for nuanced scoring
    MAX_TOKENS = 2000  # Higher for detailed scoring responses
    TIMEOUT = 30
    MAX_RETRIES = 2
    
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
