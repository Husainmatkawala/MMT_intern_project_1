import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for Forensic Image Service"""
    
    # MongoDB connection
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/travel_blog')
    
    # Flask configuration
    PORT = int(os.getenv('FORENSIC_SERVICE_PORT', 5002))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Image processing configuration
    MAX_IMAGE_SIZE_MB = 10  # Maximum image size to download
    IMAGE_DOWNLOAD_TIMEOUT = 30  # Timeout for downloading images in seconds
    TEMP_IMAGE_DIR = 'temp_images'  # Temporary directory for downloaded images
    
    # Scoring thresholds
    AI_DETECTION_THRESHOLD = 0.5  # Below this = likely AI-generated
    HIGH_CONFIDENCE_THRESHOLD = 0.7  # Above this = high confidence real
    
    # Score values
    AI_GENERATED_SCORE = -50
    NO_IMAGE_SCORE = 0
    REAL_IMAGE_SCORE = 100
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.MONGODB_URI:
            raise ValueError("MONGODB_URI must be set in environment variables")
        
        # Create temp image directory if it doesn't exist
        os.makedirs(cls.TEMP_IMAGE_DIR, exist_ok=True)
        
        return True
