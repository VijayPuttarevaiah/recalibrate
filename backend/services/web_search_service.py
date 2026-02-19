# services/web_search_service.py
import os
import requests
from datetime import datetime


SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

CURRENT_YEAR = datetime.now().year


def build_search_queries(goal: str, category: str, notes: str = None) -> list[str]:
    """Generate category-aware search queries."""
    
    queries = []
    
    if category.lower() == "immigration":
        queries = [
            f"{goal} latest requirements {CURRENT_YEAR - 1} {CURRENT_YEAR}",
            f"{goal} step by step process timeline",
            f"{goal} documents checklist fees",
        ]
    elif category.lower() == "career":
        queries = [
            f"{goal} roadmap skills required {CURRENT_YEAR}",
            f"{goal} best practices industry trends",
            f"{goal} certifications courses recommended",
        ]
    elif category.lower() == "fitness":
        queries = [
            f"{goal} workout plan schedule",
            f"{goal} science-backed approach beginners",
            f"{goal} nutrition and recovery tips",
        ]
    else:
        queries = [
            f"{goal} complete guide step by step",
            f"{goal} latest information {CURRENT_YEAR - 1} {CURRENT_YEAR}",
        ]

    if notes:
        queries.append(f"{goal} {notes}")

    return queries


def search_web(query: str, num_results: int = 5) -> list[dict]:
    """Search using Serper (Google Search API). Swap with any provider."""
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": num_results}

    try:
        resp = requests.post(SERPER_URL, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
            })
        return results
    except Exception as e:
        print(f"Search error for '{query}': {e}")
        return []


def gather_research(goal: str, category: str, notes: str = None) -> str:
    """Run multiple searches and compile into a research summary."""
    print(f"DEBUG SERPER KEY: '{SERPER_API_KEY}'")
    queries = build_search_queries(goal, category, notes)
    
    all_results = []
    seen_links = set()

    for query in queries:
        results = search_web(query)
        for r in results:
            if r["link"] not in seen_links:
                seen_links.add(r["link"])
                all_results.append(r)

    if not all_results:
        return "No web search results found. Use your own knowledge."

    # Format for LLM consumption
    research_text = "=== WEB RESEARCH RESULTS ===\n\n"
    for i, r in enumerate(all_results, 1):
        research_text += f"{i}. {r['title']}\n"
        research_text += f"   {r['snippet']}\n"
        research_text += f"   Source: {r['link']}\n\n"

    return research_text