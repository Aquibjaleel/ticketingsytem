from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any
from mcp import (
    embed_ticket,
    search_similar_tickets,
    create_embedding,
    assign_to_cluster,
    check_and_create_problem,
    build_ticket_embedding_text,
    handle_mcp_request,
    router as mcp_router #Added for AI Grouping feature
)

app = FastAPI()

app.include_router(mcp_router) ####Added for AI Grouping feature

class MCPRequest(BaseModel):
    operation: str
    ticket_id: Optional[int] = None
    query: Optional[str] = None
    top_k: Optional[int] = 5

@app.post("/mcp-embedding")
def handle_mcp(req: MCPRequest):
   # if req.operation == "embed_ticket":
   #    return embed_ticket(req.ticket)
    if req.operation == "embed_ticket":
        if req.ticket_id is None:
            raise ValueError("ticket_id is required for embed_ticket")

        return embed_ticket(int(req.ticket_id))
        
         ticket = req.ticket or {}
         ticket_id = ticket.get("id")
         #text = f"{ticket.get('subject','')} {ticket.get('description','')}"
         text = build_ticket_embedding_text(ticket)
         # Step 1: Generate embedding
         embedding = create_embedding(text)

         #  Step 2: Assign to cluster
         cluster, score = assign_to_cluster(ticket_id, text, embedding)

         #  Step 3: Check problem creation
         problem = check_and_create_problem(cluster)

         return {
            "ticket_id": ticket_id,
            "cluster_id": cluster["cluster_id"],
            "similarity_score": score,
            "cluster_size": len(cluster["tickets"]),
            "problem_created": problem is not None,
            "problem_ticket": problem
        }

    if req.operation == "search_similar_tickets":
        return search_similar_tickets(
            query=req.query,
            top_k=req.top_k
        )

    return {"error": "Unknown operation"}
