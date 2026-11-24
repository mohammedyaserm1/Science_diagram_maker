import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class AppConfig:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    DATA_DIR = BASE_DIR / "data"
    CONCEPTS_FILE = DATA_DIR / "concepts.json"
    RESULTS_FILE = DATA_DIR / "results.json"
    SVG_WIDTH = 800
    SVG_HEIGHT = 500
    GEMINI_TEMPERATURE = 0.2
    GEMINI_MAX_OUTPUT_TOKENS = 8192
    GEMINI_TIMEOUT_MS = 60000
    MINIMAL_THINKING_MODELS = {"gemini-3.5-flash", "gemini-3.5-flash-lite"}
    MAX_REVIEWER_FEEDBACK_LENGTH = 2000
    MAX_API_RETRIES = 3
    MAX_VALIDATION_RETRIES = 1
    RETRY_INITIAL_DELAY = 5
    RETRYABLE_STATUS_CODES = {429, 503}
    BATCH_GENERATION_DELAY = 10
