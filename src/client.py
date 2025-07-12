import json
from typing import Dict, Any, List
from fastmcp import Client

class GoogleRSSClient:
    """Google RSS MCP Client class"""
    
    def __init__(self, server_url: str = "http://localhost:8000/mcp/"):
        """
        Initialize the client
        
        Args:
            server_url: MCP server URL
        """
        self.server_url = server_url
        self.client = None
        self.connected = False
    
    async def connect(self):
        """Connect to the server."""
        try:
            # Use FastMCP Client to connect to the server
            self.client = Client(self.server_url)
            await self.client.__aenter__()
            self.connected = True
            print(f"Connected to MCP server: {self.server_url}")
        except Exception as e:
            print(f"Failed to connect to server: {str(e)}")
            raise
    
    async def disconnect(self):
        """Disconnect from the server."""
        if self.connected and self.client:
            await self.client.__aexit__(None, None, None)
            self.connected = False
            print("Disconnected from server.")
    
    def _parse_result(self, result) -> Any:
        """Parse FastMCP result."""
        print(f"_parse_result called. Input type: {type(result)}")
        if hasattr(result, 'content'):
            print(f"CallToolResult .content type: {type(result.content)}")
            result = result.content
        if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
            try:
                return json.loads(result[0].text)
            except Exception as e:
                print(f"JSON parsing failed: {e}")
                return []
        return result

    async def get_available_topics(self) -> List[str]:
        """
        Get a list of available Google News topics.
        
        Returns:
            List of available topics
        """
        if not self.connected:
            await self.connect()
        
        try:
            result = await self.client.call_tool("get_available_topics", {})
            parsed_result = self._parse_result(result)
            return parsed_result if isinstance(parsed_result, list) else []
        except Exception as e:
            print(f"Failed to get topic list: {str(e)}")
            return []
           
    async def search_google_news(
        self, 
        query: str, 
        max_results: int = 10,
        language: str = "ko",
        region: str = "KR"
    ) -> List[Dict[str, Any]]:
        """
        Perform a search on Google News RSS.
        
        Args:
            query: Search keyword
            max_results: Maximum number of results
            language: Language code (e.g., 'en', 'ko', 'ja', 'zh')
            region: Region code (e.g., 'US', 'KR', 'JP', 'CN')
        
        Returns:
            List of search results
        """
        if not self.connected:
            await self.connect()
        
        try:
            result = await self.client.call_tool("search_google_news", {
                "query": query,
                "max_results": max_results,
                "language": language,
                "region": region
            })
            parsed_result = self._parse_result(result)
            return parsed_result if isinstance(parsed_result, list) else []
        except Exception as e:
            print(f"Google News search failed: {str(e)}")
            return []
    
    async def get_google_news_topic(
        self, 
        topic: str = "top", 
        max_results: int = 10,
        language: str = "ko",
        region: str = "KR"
    ) -> List[Dict[str, Any]]:
        """
        Get news from a specific Google News topic.
        
        Args:
            topic: Topic category
            max_results: Maximum number of results
            language: Language code (e.g., 'en', 'ko', 'ja', 'zh')
            region: Region code (e.g., 'US', 'KR', 'JP', 'CN')
        
        Returns:
            List of news items from the specified topic
        """
        if not self.connected:
            await self.connect()
        
        try:
            result = await self.client.call_tool("get_google_news_topic", {
                "topic": topic,
                "max_results": max_results,
                "language": language,
                "region": region
            })
            parsed_result = self._parse_result(result)
            return parsed_result if isinstance(parsed_result, list) else []
        except Exception as e:
            print(f"Failed to get Google News topic: {str(e)}")
            return []
    


