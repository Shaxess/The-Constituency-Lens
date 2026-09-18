import os
from dotenv import load_dotenv

load_dotenv()

SHEET_NAME = "The Constituency Lens Raw Data"
CREDENTIALS_FILE = "credentials"
CURRENT_LGA = "Ojo"
LGA = "Ojo"
TwITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
TWITTER_DELAY = 2.5
INTERNAL_ONLY_FIELDS = ["author", "link", "handle", "user_id", "profile_url"]
SUPPORTED_LGAS = ["Ojo"]
