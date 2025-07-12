import logging
from typing import Dict, Any, List
from fastmcp import FastMCP
from src.rss import GoogleRSSTools
from fastmcp.server.middleware.timing import TimingMiddleware
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware

# Create FastMCP server instance
mcp = FastMCP(
    name="google-rss-mcp",
    instructions="This server provides tools for collecting news from Google News RSS."
)

mcp.add_middleware(TimingMiddleware())
mcp.add_middleware(LoggingMiddleware())
mcp.add_middleware(RateLimitingMiddleware())
mcp.add_middleware(ErrorHandlingMiddleware())

@mcp.tool(
    name="get_available_topics",
    description="Returns a list of available Google News topics."
)
async def get_available_topics() -> List[str]:
    """
    Returns a list of available Google News topics.
    
    Returns:
        List of available topics
    """
    return ["top", "world", "business", "technology", "entertainment", "sports", "science", "health"]

@mcp.tool(
    name="search_google_news",
    description="Performs a search on Google News RSS."
)
async def search_google_news(
    query: str, 
    max_results: int = 10, 
    language: str = "ko", 
    region: str = "KR"
) -> List[Dict[str, Any]]:
    """
    Performs a search on Google News RSS.
    
    Args:
        query: Search keyword
        max_results: Maximum number of results (default: 10)
        language: Language code (e.g., 'en', 'ko', 'ja', 'zh')
        region: Region code (e.g., 'US', 'KR', 'JP', 'CN')
    
    Returns:
        List of search results
    """
    try:
        async with GoogleRSSTools(language=language, region=region) as rss_tools:
            results = await rss_tools.search_google_news_rss(query, max_results)
            return [rss_tools.to_dict(item) for item in results]
    except Exception as e:
        print(f"Google News search failed: {str(e)}")
        return []

@mcp.tool(
    name="get_google_news_topic",
    description="Gets news from a specific Google News topic."
)
async def get_google_news_topic(
    topic: str = "top", 
    max_results: int = 10,
    language: str = "en",
    region: str = "US"
) -> List[Dict[str, Any]]:
    """
    Gets news from a specific Google News topic.
    
    Args:
        topic: Topic category (top, world, business, technology, entertainment, sports, science, health)
        max_results: Maximum number of results (default: 10)
        language: Language code (e.g., 'en', 'ko', 'ja', 'zh')
        region: Region code (e.g., 'US', 'KR', 'JP', 'CN')
    
    Returns:
        List of news items from the specified topic
    """
    try:
        async with GoogleRSSTools(language=language, region=region) as rss_tools:
            results = await rss_tools.get_google_news_topics(topic, max_results)
            return [rss_tools.to_dict(item) for item in results]
    except Exception as e:
        print(f"Failed to get Google News topic: {str(e)}")
        return []

if __name__ == "__main__":
    mcp.run(transport="stdio")