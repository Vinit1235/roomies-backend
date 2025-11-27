import feedparser
import ssl

class NewsService:
    def __init__(self):
        # Using Times of India Education RSS Feed as a source
        self.rss_url = "https://timesofindia.indiatimes.com/rssfeeds/913168846.cms"
        
        # Handle SSL certificate issues if any
        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context

    def get_latest_news(self, limit=5):
        try:
            feed = feedparser.parse(self.rss_url)
            news_items = []
            
            for entry in feed.entries[:limit]:
                # Extract image if available (some feeds have it in media_content or summary)
                image_url = None
                if 'media_content' in entry:
                    image_url = entry.media_content[0]['url']
                
                news_items.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': entry.published,
                    'summary': entry.summary,
                    'image': image_url
                })
                
            return news_items
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
