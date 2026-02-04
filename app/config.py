import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MONGODB_SETTINGS = {
        "host": os.getenv("MONGO_URI")
    }
    SECRET_KEY = os.getenv("SECRET_KEY")
    SPEECHMATICS_API_KEY = os.getenv("SPEECHMATICS_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SM_URL = "wss://eu.rt.speechmatics.com/v2"
    HEADER_LEN = 5