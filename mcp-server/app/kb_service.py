import json
import re
from pathlib import Path

KB_PATH = Path(__file__).resolve().parent / "knowledge_base.json"


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def load_knowledge_base():
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def score_article(ticket_title: str, ticket_description: str, ticket_category: str, article: dict) -> int:
    score = 0

    title_text = normalize(ticket_title)
    desc_text = normalize(ticket_description)
    full_text = f"{title_text} {desc_text}"
    category_text = normalize(ticket_category)

    article_category = normalize(article.get("category", ""))
    article_title = normalize(article.get("title", ""))
    article_keywords = [normalize(k) for k in article.get("keywords", [])]

    if category_text and category_text == article_category:
        score += 3

    for kw in article_keywords:
        if kw and kw in full_text:
            score += 2

    for word in article_title.split():
        if len(word) > 3 and word in full_text:
            score += 1

    return score


# to get top N articles based on scoring function

def get_top_articles(ticket_title: str, ticket_description: str, ticket_category: str, top_n: int = 3):
    kb = load_knowledge_base()
    scored_articles = []

    print("\n=== ALL ARTICLES DEBUG ===")
    print("Requested top_n:", top_n)

    for article in kb:
        score = score_article(ticket_title, ticket_description, ticket_category, article)
        print(f"{article['id']} | {article['title']} | score={score}")
        scored_articles.append({
            "score": score,
            "article": article
        })

    scored_articles.sort(key=lambda x: x["score"], reverse=True)

    selected = [item["article"] for item in scored_articles[:top_n]]

    print("\n=== SELECTED TOP 3 ARTICLES BASED ON SCORING ===")
    for article in selected:
        print(f"{article['id']} | {article['title']}")

    return selected