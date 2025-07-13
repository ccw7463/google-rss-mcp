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
    instructions="This server provides tools for collecting news from Google News RSS"
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
    topics = ["top", "world", "business", "technology", "entertainment", "sports", "science", "health"]
    return topics

@mcp.tool(
    name="search_news",
    description="Search for news articles and extract their content in one operation."
)
async def search_news(
    query: str, 
    max_results: int = 5,
    max_length: int = 4000
) -> List[Dict[str, Any]]:
    """
    Search for news articles and extract their content in one operation.
    
    This method performs RSS search and content extraction in a single call,
    returning comprehensive article information including title, URL, content,
    and publication date.
    
    Args:
        query: Search query for news articles
        max_results: Maximum number of results to return (default: 5)
        max_length: Maximum length of article content in characters (default: 4000)
    
    Returns:
        List of article information dictionaries containing:
            - article_title: Title of the article
            - article_url: URL of the article
            - article_content: Extracted content of the article
            - article_published: Publication date
            - user_query: Original search query
    """
    
    try:
        async with GoogleRSSTools() as rss_tools:
            results = await rss_tools.search_news(query, max_results, max_length)
            return results
    except Exception as e:
        logging.error(f"Error in search_news: {str(e)}")
        return []

@mcp.tool(
    name="search_specific_topic_news",
    description="Search for news articles from specific topics and extract their content."
)
async def search_specific_topic_news(
    topic: str = "top", 
    max_results: int = 5,
    max_length: int = 4000
) -> List[Dict[str, Any]]:
    """
    Search for news articles from specific topics and extract their content.
    
    This method retrieves news from predefined topic categories such as top stories,
    world news, business, technology, etc.
    
    Args:
        topic: Topic category to search for. Supported topics:
            - "top": Top stories
            - "world": World news
            - "business": Business news
            - "technology": Technology news
            - "entertainment": Entertainment news
            - "sports": Sports news
            - "science": Science news
            - "health": Health news
        max_results: Maximum number of results to return (default: 5)
        max_length: Maximum length of article content in characters (default: 4000)
    
    Returns:
        List of article information dictionaries containing:
            - article_title: Title of the article
            - article_url: URL of the article
            - article_content: Extracted content of the article
            - article_published: Publication date
            - topic: Original topic category
    """
    
    try:
        async with GoogleRSSTools() as rss_tools:
            results = await rss_tools.search_specific_topic_news(topic, max_results, max_length)
            return results
    except Exception as e:
        logging.error(f"Error in search_specific_topic_news: {str(e)}")
        return []

if __name__ == "__main__":
    mcp.run(transport="stdio")