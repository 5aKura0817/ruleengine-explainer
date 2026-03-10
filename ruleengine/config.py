import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv('API_BASE_URL', 'https://data.ct108.net/ncs-ruleengine-api')
TEAMID = os.getenv('TEAMID', '93')
NCS_USER_TOKEN = os.getenv('NCS_USER_TOKEN', '')

# Validation
if not NCS_USER_TOKEN:
    raise ValueError("NCS_USER_TOKEN not found in environment variables. Please set it in .env file.")
