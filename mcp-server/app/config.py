import os

#AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
#AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
#AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_API_VERSION = "2024-02-15-preview"
EMBEDDING_MODEL = os.getenv("My-embedding-model")

debug_mode = os.getenv("DEBUG", "False")

DB_PATH = os.getenv("TICKETS_DB_PATH") or os.path.abspath("C:\\Users\\navik\\Desktop\\DevOps\\GitHub\\av\\flicket_app_with_ai_features\\flicket_app_with_ai_features\\flicket.db")

SYSTEM_PROMPT = "You are a helpful assistant."
MAX_TOKENS = 200
