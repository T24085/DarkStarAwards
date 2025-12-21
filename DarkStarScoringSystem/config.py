"""Configuration management for DSSS worker."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # Firebase
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'darkstarawards')
    FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS_JSON', './credentials/firebase-service-account.json')
    STORAGE_BUCKET = os.getenv('STORAGE_BUCKET', 'darkstarawards.firebasestorage.app')
    
    # Ollama
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')
    
    # Worker
    POLL_INTERVAL_SECONDS = int(os.getenv('POLL_INTERVAL_SECONDS', '600'))
    JUDGE_VERSION = os.getenv('JUDGE_VERSION', 'v1.0')
    MAX_JOB_MINUTES = int(os.getenv('MAX_JOB_MINUTES', '7'))
    MAX_CONCURRENT_JOBS = int(os.getenv('MAX_CONCURRENT_JOBS', '1'))
    
    # Timeouts
    NAVIGATION_TIMEOUT_MS = int(os.getenv('NAVIGATION_TIMEOUT_MS', '60000'))
    TOTAL_JOB_TIMEOUT_SECONDS = int(os.getenv('TOTAL_JOB_TIMEOUT_SECONDS', '420'))
    
    # Paths
    BASE_DIR = Path(__file__).parent
    ARTIFACTS_DIR = BASE_DIR / 'artifacts'
    ARTIFACTS_DIR.mkdir(exist_ok=True)
    
    # Firestore Collections
    SUBMISSIONS_COLLECTION = 'entries'
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not Path(cls.FIREBASE_CREDENTIALS_JSON).exists():
            raise FileNotFoundError(f"Firebase credentials not found: {cls.FIREBASE_CREDENTIALS_JSON}")

