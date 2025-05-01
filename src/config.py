import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set. Please create a .env file with your API key.")

# Other configuration
BACKEND_PORT = 5000
CORS_ORIGINS = ["chrome-extension://*"] 