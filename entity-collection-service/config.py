import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (parent of entity-collection-service)
project_root = Path(__file__).parent.parent

# Load backend/.env
backend_env_path = project_root / 'backend' / '.env'
if backend_env_path.exists():
    load_dotenv(backend_env_path, override=False)

# Also try loading from current directory if .env exists
load_dotenv(override=False)

class Config:
    """Configuration class for Entity Collection Service"""
    
    # MongoDB Configuration (from backend/.env)
    MONGODB_URI = os.getenv('MONGODB_URI')
    
    # Server Configuration
    PORT = int(os.getenv('ENTITY_COLLECTION_SERVICE_PORT', 5006))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            'MONGODB_URI'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
