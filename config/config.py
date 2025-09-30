"""
Configuration module for GIS Traffic Sign Automation Bot
"""
import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class"""
    
    # WordPress/Site Configuration
    SITE_URL = os.getenv('SITE_URL', '')
    LOGIN_URL = os.getenv('LOGIN_URL', '')
    USERNAME = os.getenv('LOGIN_USERNAME', '')
    PASSWORD = os.getenv('PASSWORD', '')
    
    # GIS Admin URLs
    GIS_ADMIN_URL = os.getenv('GIS_ADMIN_URL', '')
    TRAFFIC_SIGNS_URL = os.getenv('TRAFFIC_SIGNS_URL', '')
    
    # Browser Configuration
    BROWSER_TYPE = os.getenv('BROWSER_TYPE', 'chrome').lower()
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
    WAIT_TIMEOUT = int(os.getenv('WAIT_TIMEOUT', '30'))
    IMPLICIT_WAIT = int(os.getenv('IMPLICIT_WAIT', '10'))
    
    # Image Processing
    IMAGE_FOLDER = os.getenv('IMAGE_FOLDER', './images')
    SUPPORTED_FORMATS = os.getenv('SUPPORTED_FORMATS', 'jpg,jpeg,png,bmp').split(',')
    MAX_IMAGE_SIZE_MB = int(os.getenv('MAX_IMAGE_SIZE_MB', '10'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/bot.log')
    
    # AI/ML (Optional)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    USE_AI_ANALYSIS = os.getenv('USE_AI_ANALYSIS', 'false').lower() == 'true'
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate required configuration values"""
        required_fields = [
            'SITE_URL', 'LOGIN_URL', 'USERNAME', 'PASSWORD'
        ]
        
        missing_fields = [field for field in required_fields if not getattr(cls, field)]
        
        if missing_fields:
            print(f"Missing required configuration: {', '.join(missing_fields)}")
            return False
        
        return True
    
    @classmethod
    def get_browser_options(cls) -> Dict:
        """Get browser-specific options"""
        options = {
            'headless': cls.HEADLESS_MODE,
            'window_size': '1920,1080',
            'disable_dev_shm_usage': True,
            'no_sandbox': True,
            'disable_gpu': cls.HEADLESS_MODE
        }
        
        return options


class TrafficSignAttributes:
    """Configuration for traffic sign attributes and their possible values"""
    
    # Common traffic sign materials
    MATERIALS = [
        'aluminum',
        'steel',
        'plastic',
        'composite',
        'reflective_sheeting'
    ]
    
    # Stand/Post types
    STAND_TYPES = [
        'metal_post',
        'wooden_post',
        'concrete_post',
        'u_channel_post',
        'square_tube_post',
        'round_post'
    ]
    
    # Sign conditions
    CONDITIONS = [
        'excellent',
        'good',
        'fair',
        'poor',
        'damaged',
        'needs_replacement'
    ]
    
    # Sign sizes (common dimensions)
    SIZES = [
        '600x600mm',
        '750x750mm',
        '900x900mm',
        '600x300mm',
        '900x600mm',
        'custom'
    ]
    
    # Installation methods
    INSTALLATION_METHODS = [
        'bolted',
        'welded',
        'clamped',
        'banded'
    ]
    
    @classmethod
    def get_all_attributes(cls) -> Dict[str, List[str]]:
        """Get all attribute categories and their possible values"""
        return {
            'materials': cls.MATERIALS,
            'stand_types': cls.STAND_TYPES,
            'conditions': cls.CONDITIONS,
            'sizes': cls.SIZES,
            'installation_methods': cls.INSTALLATION_METHODS
        }


# Create directories if they don't exist
def ensure_directories():
    """Ensure required directories exist"""
    directories = [
        Config.IMAGE_FOLDER,
        os.path.dirname(Config.LOG_FILE),
        'src',
        'bot'
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


# Initialize directories on import
ensure_directories()
