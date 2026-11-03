"""Web search service supporting live DuckDuckGo, Tavily, and SerpAPI providers with Gemini grounding."""

import logging
from typing import Any, Dict, List, Optional
import httpx
from duckduckgo_search import DDGS

from app.core.config import settings
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class WebSearchService:
    """Performs live web search and generates source-grounded summaries."""

    def __init__(self):
        self.provider = settings.SEARCH_PROVIDER.lower()
        self.tavily_key = settings.TAVILY_API_KEY
        self.serpapi_key = settings.SERPAPI_API_KEY

    async def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform search using DuckDuckGo (no API key required)."""
        results: List[Dict[str, Any]] = []
        try:
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, max_results=max_results))
                for item in ddg_results:
                    results.append(
                        {
                            "title": item.get("title", "No Title"),
                            "url": item.get("href") or item.get("url", ""),
                            "snippet": item.get("body", ""),
                            "published_date": item.get("date"),
                        }
                    )
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            raise RuntimeError(f"DuckDuckGo search failed: {str(e)}")

        return results

    async def _search_tavily(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform search using Tavily API."""
        if not self.tavily_key:
            raise ValueError("Tavily API key is not configured. Set TAVILY_API_KEY in backend/.env")

        results: List[Dict[str, Any]] = []
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_key,
            "query": query,
            "max_results": max_results,
            "include_answer": False,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("results", []):
                results.append(
                    {
                        "title": item.get("title", "No Title"),
                        "url": item.get("url", ""),
                        "snippet": item.get("content", ""),
                        "published_date": item.get("published_date"),
                    }
                )
        return results

    async def _search_serpapi(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform search using SerpAPI."""
        if not self.serpapi_key:
            raise ValueError("SerpAPI key is not configured. Set SERPAPI_API_KEY in backend/.env")

        results: List[Dict[str, Any]] = []
        url = "https://serpapi.com/search.json"
        params = {
            "q": query,
            "api_key": self.serpapi_key,
            "num": max_results,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("organic_results", []):
                results.append(
                    {
                        "title": item.get("title", "No Title"),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "published_date": item.get("date"),
                    }
                )
        return results

    async def search_and_ground(
        self,
        query: str,
        depth: str = "standard",
        max_results: int = 5,
    ) -> Dict[str, Any]:
        """Perform web search and synthesize with Gemini model."""
        if depth == "quick":
            limit = min(max_results, 3)
        elif depth == "deep":
            limit = min(max_results, 8)
        else:
            limit = max_results

        # Execute search with configured provider
        sources: List[Dict[str, Any]] = []
        provider_used = self.provider

        if self.provider == "tavily" and self.tavily_key:
            sources = await self._search_tavily(query, max_results=limit)
        elif self.provider == "serpapi" and self.serpapi_key:
            sources = await self._search_serpapi(query, max_results=limit)
        else:
            # Default to DuckDuckGo (always functional, no key needed)
            provider_used = "duckduckgo"
            sources = await self._search_duckduckgo(query, max_results=limit)

        if not sources:
            return {
                "query": query,
                "summary": f"No live search results were found for query: '{query}'.",
                "sources": [],
                "provider": provider_used,
                "depth": depth,
            }

        # Format sources for Gemini synthesis
        context_items = []
        for i, src in enumerate(sources, 1):
            date_str = f" ({src['published_date']})" if src.get("published_date") else ""
            context_items.append(
                f"[{i}] {src['title']}{date_str}\nURL: {src['url']}\nSnippet: {src['snippet']}"
            )
        context_str = "\n\n".join(context_items)

        system_instruction = (
            "You are DARZFUSION AI's Web Research Assistant. "
            "Synthesize an informative, accurate, and comprehensive answer to the user's question "
            "based strictly on the provided web search results. "
            "Cite each claim with source brackets (e.g. [1], [2]) linking to the corresponding source. "
            "Keep external sources clearly attributed and do not invent details not supported by the sources."
        )

        prompt = (
            f"LIVE SEARCH RESULTS:\n{context_str}\n\n"
            f"USER QUERY:\n{query}\n\n"
            f"SYNTHESIS & SUMMARY:"
        )

        summary = await gemini_service.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.3,
        )

        return {
            "query": query,
            "summary": summary,
            "sources": sources,
            "provider": provider_used,
            "depth": depth,
        }


web_search_service = WebSearchService()
