
############ THIS WILL NEED SOME TROUBLESHOOTING, CURRENTLY MULTIPLE BRANCHES CHANGES ON THIS ############

from openai import AzureOpenAI
from app.config import (
    EMBEDDING_MODEL,
    OPENAI_API_KEY

from config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_API_VERSION,
    MAX_TOKENS,
)

client = AzureOpenAI(
    api_key=OPENAI_API_KEY,
    azure_endpoint="endpointURL",
    api_version="2024-02-15-preview"
)

<<<<<<< HEAD
def create_embedding(text: str) -> list[float]:
    """
    Generate numeric embedding vector for text
    """
    global client
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
=======
def call_model(system_prompt, user_prompt):
    print("ENDPOINT:", repr(AZURE_OPENAI_ENDPOINT))
    print("DEPLOYMENT:", repr(AZURE_OPENAI_DEPLOYMENT))
    print("API_KEY_SET:", bool(AZURE_OPENAI_API_KEY))
    print("API_VERSION:", repr(AZURE_OPENAI_API_VERSION))

    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_completion_tokens=MAX_TOKENS,
>>>>>>> origin/KB_article_AI
    )

    # Always numeric float list
    return response.data[0].embedding
