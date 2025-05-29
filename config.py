import os
import google.generativeai as genai

OPENAI_API_KEY = "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"
GOOGLE_API_KEY = "AIzaSyB1tzxthWeGBv_TGwOOcjEgKwJWyMphN6E"

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Get the directory where this config.py file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use absolute paths for all file references
DB_PATH = os.path.join(BASE_DIR, "chroma_poetry_db")
POETRY_DATA_FILE = os.path.join(BASE_DIR, "PoetryFoundationData.csv") 