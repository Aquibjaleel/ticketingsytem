import json
import math
import sqlite3
from mcp.server.fastmcp import FastMCP
from .openai_client import create_embedding, call_model
from .db_conn import get_db_connection
from .kb_service import get_top_articles
from .config import SYSTEM_PROMPT

# Initialize FastMCP
mcp = FastMCP("Ticketing-Auditor")

# --- UTILS ---
def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

# --- TOOLS ---

@mcp.tool()
def search_similar_tickets(query: str, top_k: int = 5) -> dict:
    """Finds existing tickets that match a new query using vector similarity."""
    query_embedding = create_embedding(query)
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    try:
        cursor.execute("SELECT id, title, embedding FROM flicket_topic WHERE embedding IS NOT NULL")
        tickets = cursor.fetchall()
        results = []

        for tid, title, emb_json in tickets:
            ticket_embedding = json.loads(emb_json)
            score = cosine_similarity(query_embedding, ticket_embedding)
            results.append({
                "ticket_id": tid,
                "description": title,
                "similarity_score": round(float(score), 4)
            })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return {"matches": results[:top_k]}
    finally:
        db_conn.close()

@mcp.tool()
def suggest_kb_articles(ticket_title: str, ticket_description: str, ticket_category: str) -> dict:
    """Combines keyword search and AI to find the best KB article for a ticket."""
    
    # 1. Get candidates from the KB Service
    candidate_articles = get_top_articles(
        ticket_title=ticket_title,
        ticket_description=ticket_description,
        ticket_category=ticket_category,
        top_n=3
    )

    if not candidate_articles:
        return {"error": "No matching knowledge article found."}

    # 2. Build AI Prompt for selection
    article_text = ""
    for idx, art in enumerate(candidate_articles, start=1):
        article_text += f"Article {idx} (ID: {art.get('id')}): {art.get('title')}\nSteps: {art.get('steps')}\n"

    kb_prompt = f"""
    Compare this Ticket to the Knowledge Articles and pick the BEST match.
    Ticket: {ticket_title} - {ticket_description}
    Candidates: {article_text}
    Return JSON only: {{"suggested_article_id": "", "confidence": "high|medium|low", "reason": ""}}
    """

    # 3. Use AI to pick the best one
    ai_decision = call_model(SYSTEM_PROMPT, kb_prompt)
    try:
        return json.loads(ai_decision)
    except:
        return {"raw_ai_output": ai_decision}

@mcp.tool()
def embed_ticket(ticket_id: int) -> dict:
    """Generates and saves a vector embedding for a specific ticket ID."""
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    
    try:
        # Fetch ticket details
        cursor.execute("SELECT title, content FROM flicket_topic WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        if not row: return {"error": "Not found"}

        # Embed
        text = f"Subject: {row[0]}\nDescription: {row[1]}"
        embedding = create_embedding(text)

        # Persist
        cursor.execute("UPDATE flicket_topic SET embedding = ? WHERE id = ?", (json.dumps(embedding), ticket_id))
        db_conn.commit()
        return {"status": "success", "ticket_id": ticket_id}
    finally:
        db_conn.close()