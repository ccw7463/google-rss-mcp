from src.client import GoogleRSSClient
import asyncio
import logging

logger = logging.getLogger(__name__)

async def main():
    """Main function - Client usage example"""
    client = GoogleRSSClient()
    
    try:
        # Connect to server
        await client.connect()
        
        # Check available topics
        topics = await client.get_available_topics()
        print(f"Available topics: {topics}")
        
        # Google News search
        print("\n=== Google News Search ===")
        search_results = await client.search_google_news("artificial intelligence", 5)
        print("search_results:", search_results)
        for i, item in enumerate(search_results):
            print(f"{i+1}th article")
            print("item:", item)
            print(f"Title: {item.get('title', 'No title')}")
            print(f"Link: {item.get('link', 'No link')}")
            print(f"Description: {item.get('description', 'No description')[:100]}...")
        
        # Get news from specific topic
        print("\n=== Technology News ===")
        tech_news = await client.get_google_news_topic("technology", 3)
        for i, item in enumerate(tech_news):
            print(f"{i+1}th article")
            print("item:", item)
            print(f"Title: {item.get('title', 'No title')}")
            print(f"Link: {item.get('link', 'No link')}")
            print(f"Description: {item.get('description', 'No description')[:100]}...")
        
    except Exception as e:
        logger.error(f"Error during client execution: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
