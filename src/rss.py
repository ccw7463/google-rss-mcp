import feedparser
import requests
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RSSItem:
    """Data class representing an RSS item"""
    title: str
    link: str
    description: str
    published: Optional[datetime] = None
    author: Optional[str] = None
    category: Optional[str] = None
    source: str = ""

@dataclass
class RSSFeed:
    """Data class representing an RSS feed"""
    title: str
    link: str
    description: str
    language: Optional[str] = None
    last_updated: Optional[datetime] = None
    items: List[RSSItem] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []

class GoogleRSSTools:
    """Tool class for processing Google RSS feeds"""
    
    def __init__(self, language: str = "ko", region: str = "KR"):
        """
        Initialize GoogleRSSTools with language and region settings.
        
        Args:
            language (str): Language code (e.g., 'en', 'ko', 'ja', 'zh')
            region (str): Region code (e.g., 'US', 'KR', 'JP', 'CN')
        """
        self.session = None
        self.language = language
        self.region = region
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats."""
        if not date_str:
            return None
        
        # Let feedparser attempt automatic parsing
        try:
            parsed_date = feedparser._parse_date(date_str)
            if parsed_date:
                return datetime.fromtimestamp(parsed_date, tz=timezone.utc)
        except:
            pass
        
        # Manual parsing attempts
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Remove HTML tags and clean text."""
        if not text:
            return ""
        
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading and trailing whitespace
        return text.strip()
    
    async def fetch_rss_feed(self, feed_url: str) -> RSSFeed:
        """Fetch and parse an RSS feed."""
        try:
            if self.session:
                async with self.session.get(feed_url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {feed_url}")
                    content = await response.text()
            else:
                response = requests.get(feed_url, headers=self.headers)
                response.raise_for_status()
                content = response.text
            
            # Parse with feedparser
            parsed = feedparser.parse(content)
            
            # Extract feed metadata
            feed_info = parsed.feed
            feed = RSSFeed(
                title=feed_info.get('title', ''),
                link=feed_info.get('link', ''),
                description=feed_info.get('description', ''),
                language=feed_info.get('language'),
                last_updated=self._parse_date(feed_info.get('updated', ''))
            )
            
            # Parse items
            for entry in parsed.entries:
                item = RSSItem(
                    title=self._clean_text(entry.get('title', '')),
                    link=entry.get('link', ''),
                    description=self._clean_text(entry.get('description', '')),
                    published=self._parse_date(entry.get('published', '')),
                    author=entry.get('author', ''),
                    category=entry.get('category', ''),
                    source=feed.title
                )
                feed.items.append(item)
            
            logger.info(f"Retrieved {len(feed.items)} items from RSS feed '{feed.title}'.")
            return feed
            
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed: {feed_url} - {str(e)}")
            raise
    
    async def search_google_news_rss(self, query: str, max_results: int = 10) -> List[RSSItem]:
        """Perform Google News RSS search."""
        # Construct Google News RSS URL with language and region settings
        encoded_query = requests.utils.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl={self.language}&gl={self.region}&ceid={self.region}:{self.language}"
        
        try:
            feed = await self.fetch_rss_feed(rss_url)
            return feed.items[:max_results]
        except Exception as e:
            logger.error(f"Google News RSS search failed: {str(e)}")
            return []
    
    async def get_google_news_topics(self, topic: str = "top", max_results: int = 10) -> List[RSSItem]:
        """Get specific topics from Google News."""
        topic_urls = {
            "top": f"https://news.google.com/rss?hl={self.language}&gl={self.region}&ceid={self.region}:{self.language}",
            "world": f"https://news.google.com/rss/headlines/section/topic/WORLD?hl={self.language}&gl={self.region}&ceid={self.region}:{self.language}",
            "business": f"https://news.google.com/rss/headlines/section/topic/BUSINESS?hl={self.language}&gl={self.region}&ceid={self.region}:{self.language}",
            "technology": f"https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl={self.language}&gl={self.region}&ceid={self.region}:{self.language}",
            "entertainment": f"https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl={self.language}&gl={self.region}&ceid={self.region}:{self.language}",
            "sports": f"https://news.google.com/rss/headlines/section/topic/SPORTS?hl={self.language}&gl={self.region}&ceid={self.region}:{self.language}",
            "science": f"https://news.google.com/rss/headlines/section/topic/SCIENCE?hl={self.language}&gl={self.region}&ceid={self.region}:{self.language}",
            "health": f"https://news.google.com/rss/headlines/section/topic/HEALTH?hl={self.language}&gl={self.region}&ceid={self.region}:{self.language}"
        }
        
        if topic not in topic_urls:
            raise ValueError(f"Unsupported topic: {topic}. Supported topics: {list(topic_urls.keys())}")
        
        try:
            feed = await self.fetch_rss_feed(topic_urls[topic])
            return feed.items[:max_results]
        except Exception as e:
            logger.error(f"Failed to get Google News topic: {str(e)}")
            return []
    
    def to_dict(self, obj) -> Dict[str, Any]:
        """Convert object to dictionary."""
        if isinstance(obj, (RSSFeed, RSSItem)):
            result = asdict(obj)
            # Convert datetime objects to strings
            for key, value in result.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
            return result
        return obj
