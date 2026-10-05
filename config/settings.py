import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Configuration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# --- Model names ---
GEMINI_MODEL = "gemini-1.5-flash"
OPENAI_MODEL = "gpt-4o-mini"

# --- Embedding Configuration ---
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# --- Chunking Configuration ---
CHUNK_SIZE = 800
CHUNK_OVERLAP = 200

# --- ChromaDB ---
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

# --- Database ---
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "evaluation.db")

# --- Evaluation thresholds (similarity scores) ---
STRICTNESS_THRESHOLDS = {
    "easy": {
        "fill_blank_threshold": 60,
        "subjective_similarity_weight": 0.4,
        "subjective_llm_weight": 0.6,
        "partial_credit_floor": 0.3,
    },
    "medium": {
        "fill_blank_threshold": 75,
        "subjective_similarity_weight": 0.5,
        "subjective_llm_weight": 0.5,
        "partial_credit_floor": 0.15,
    },
    "hard": {
        "fill_blank_threshold": 85,
        "subjective_similarity_weight": 0.5,
        "subjective_llm_weight": 0.5,
        "partial_credit_floor": 0.0,
    },
}

# --- Upload limits ---
MAX_PDF_SIZE_MB = 50
MAX_PDFS_PER_EXAM = 10
