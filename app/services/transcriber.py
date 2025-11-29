# app/services/transcriber.py
import re
import logging
from typing import Dict, Optional, List
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# For YouTube
try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

# For Articles
try:
    from newspaper import Article
    import trafilatura
except ImportError:
    Article = None
    trafilatura = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class YouTubeTranscriber:
    """Specialized YouTube transcript extractor."""
    
    @staticmethod
    def get_video_id(url: str) -> Optional[str]:
        """Extract YouTube video ID from various URL formats."""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$',
            r'youtu\.be\/([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    @staticmethod
    def get_transcript(video_id: str, languages: List[str] = None) -> Dict:
        """
        Get YouTube transcript as clean text using youtube-transcript-api 1.2.3 style API.
        
        Args:
            video_id: YouTube video ID
            languages: Preferred languages (default: ['en'])
            
        Returns:
            Dict with 'text' (full paragraph), 'entries' (timestamped), 'language'
        """
        if not YouTubeTranscriptApi:
            raise ImportError("youtube-transcript-api not installed")
        
        if languages is None:
            languages = ['en']
        
        try:
            ytt_api = YouTubeTranscriptApi()

            # Get list of transcripts for the video
            transcript_list = ytt_api.list(video_id)

            transcript = None
            selected_language = None
            is_generated = None
            is_translatable = None

            # Prefer manually created transcripts in requested languages
            for lang in languages:
                try:
                    t = transcript_list.find_transcript([lang])
                    transcript = t
                    selected_language = t.language_code
                    is_generated = t.is_generated
                    is_translatable = t.is_translatable
                    break
                except Exception:
                    continue

            # Fallback: auto-generated transcripts in requested languages
            if not transcript:
                try:
                    t = transcript_list.find_generated_transcript(languages)
                    transcript = t
                    selected_language = t.language_code
                    is_generated = True
                    is_translatable = t.is_translatable
                except Exception:
                    pass

            # Last resort: first available transcript
            if not transcript:
                available = list(transcript_list)
                if available:
                    transcript = available[0]
                    selected_language = transcript.language_code
                    is_generated = transcript.is_generated
                    is_translatable = transcript.is_translatable

            if not transcript:
                raise Exception("No transcript available for this video")

            # Fetch transcript data
            fetched = transcript.fetch()

            # 1.2.x returns a FetchedTranscript object; normalize to list[dict]
            if hasattr(fetched, "to_raw_data"):
                raw_data = fetched.to_raw_data()
            else:
                # In case some future version returns plain list already
                raw_data = fetched

            # Convert to clean paragraph text
            full_text = YouTubeTranscriber._format_as_paragraph(raw_data)
            
            # Create timestamped entries
            entries = [
                {
                    "text": entry['text'],
                    "start": entry['start'],
                    "end": entry['start'] + entry.get('duration', 0),
                    "confidence": 0.9 if is_generated else 1.0
                }
                for entry in raw_data
            ]
            
            return {
                "text": full_text,
                "entries": entries,
                "language": selected_language or "unknown",
                "is_generated": is_generated if is_generated is not None else True,
                "is_translatable": bool(is_translatable) if is_translatable is not None else True
            }
        
        except Exception as e:
            logger.error(f"Error fetching YouTube transcript: {e}")
            raise
    
    @staticmethod
    def _format_as_paragraph(transcript_data: List[Dict]) -> str:
        """Convert transcript entries to clean paragraph text."""
        # Extract all text
        text_parts = [entry['text'].strip() for entry in transcript_data]
        
        # Join with spaces
        full_text = " ".join(text_parts)
        
        # Clean up spacing
        full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces to single
        full_text = re.sub(r'\s+([.,!?;:])', r'\1', full_text)  # Remove space before punctuation
        full_text = re.sub(r'([.,!?;:])\s*', r'\1 ', full_text)  # Ensure space after punctuation
        
        # Remove extra spaces
        full_text = full_text.strip()
        
        return full_text
    
    @staticmethod
    def get_video_metadata(video_id: str) -> Dict:
        """Get basic video metadata using YouTube's oEmbed API."""
        try:
            url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "title": data.get("title", "YouTube Video"),
                    "author": data.get("author_name", "Unknown"),
                    "thumbnail": data.get("thumbnail_url", "")
                }
        except Exception as e:
            logger.warning(f"Could not fetch video metadata: {e}")
        
        return {
            "title": "YouTube Video",
            "author": "Unknown",
            "thumbnail": ""
        }


class ContentTranscriber:
    """Extract and normalize content from various URL types."""
    
    def __init__(self):
        self.youtube_transcriber = YouTubeTranscriber()
    
    def process_url(self, url: str, beliefs: Optional[List] = None) -> Dict:
        """Main entry point: Process URL and return normalized format."""
        try:
            content_type = self._detect_content_type(url)
            logger.info(f"Detected content type: {content_type} for URL: {url}")
            
            if content_type == "youtube":
                return self._process_youtube(url, beliefs)
            elif content_type == "twitter":
                return self._process_twitter(url, beliefs)
            elif content_type == "article":
                return self._process_article(url, beliefs)
            else:
                return self._create_error_response(
                    f"Invalid URL type. Supported: YouTube, Twitter/X, Articles"
                )
        
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return self._create_error_response(f"Failed to process URL: {str(e)}")
    
    def _detect_content_type(self, url: str) -> str:
        """Detect the type of content from URL."""
        parsed = urlparse(url.lower())
        domain = parsed.netloc
        
        if any(yt in domain for yt in ['youtube.com', 'youtu.be', 'm.youtube.com']):
            return "youtube"
        
        if any(tw in domain for tw in ['twitter.com', 'x.com', 'mobile.twitter.com']):
            return "twitter"
        
        if domain and parsed.scheme in ['http', 'https']:
            return "article"
        
        return "invalid"
    
    def _process_youtube(self, url: str, beliefs: Optional[List]) -> Dict:
        """Extract YouTube video transcript as clean paragraph."""
        if not YouTubeTranscriptApi:
            return self._create_error_response(
                "YouTube processing not available. Install: pip install youtube-transcript-api"
            )
        
        try:
            # Extract video ID
            video_id = self.youtube_transcriber.get_video_id(url)
            print('video id ',video_id)
            if not video_id:
                return self._create_error_response("Could not extract YouTube video ID from URL")
            
            logger.info(f"Extracting transcript for YouTube video: {video_id}")
            
            # Get transcript
            transcript_result = self.youtube_transcriber.get_transcript(
                video_id, 
                languages=['en', 'en-US', 'en-GB']
            )
            
            # Get video metadata
            metadata = self.youtube_transcriber.get_video_metadata(video_id)
            
            logger.info(f"Successfully extracted {len(transcript_result['text'])} characters")
            entries = transcript_result["entries"]
            full_text = " ".join(entry["text"].strip() for entry in entries)
            return {
                "status": "Success",
                "content_type": "youtube",
                "transcript": {
                    "text": full_text,
                    "words": full_text
                },
                "metadata": {
                    "source_type": "youtube",
                    "content_length": len(transcript_result['text']),
                    "language_code": transcript_result['language'],
                    "title": metadata['title'],
                    "author": metadata['author'],
                    "url": url,
                    "video_id": video_id,
                    "is_auto_generated": transcript_result['is_generated']
                },
                "beliefs": beliefs or []
            }
        
        except Exception as e:
            logger.error(f"YouTube processing error: {e}")
            return self._create_error_response(f"Failed to extract YouTube transcript: {str(e)}")
    
    def _process_twitter(self, url: str, beliefs: Optional[List]) -> Dict:
        """Extract Twitter/X tweet content."""
        try:
            tweet_id = self._extract_tweet_id(url)
            if not tweet_id:
                return self._create_error_response("Could not extract tweet ID")
            
            logger.info(f"Extracting tweet: {tweet_id}")
            text, created_at = self._scrape_tweet(url)
            
            if not text:
                return self._create_error_response("Could not extract tweet content")
            
            return {
                "status": "Success",
                "content_type": "twitter",
                "transcript": {
                    "text": text,
                    "words": []
                },
                "metadata": {
                    "source_type": "twitter",
                    "content_length": len(text),
                    "language_code": "en",
                    "tweet_id": tweet_id,
                    "url": url,
                    "created_at": created_at
                },
                "beliefs": beliefs or []
            }
        
        except Exception as e:
            logger.error(f"Twitter processing error: {e}")
            return self._create_error_response(f"Failed to extract tweet: {str(e)}")
    
    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """Extract tweet ID from Twitter/X URL."""
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else None
    
    def _scrape_tweet(self, url: str) -> tuple:
        """Scrape tweet content from page."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            og_description = soup.find('meta', property='og:description')
            if og_description:
                text = og_description.get('content', '')
                return text, None
            
            return "", None
        
        except Exception as e:
            logger.error(f"Tweet scraping error: {e}")
            return "", None
    
    def _process_article(self, url: str, beliefs: Optional[List]) -> Dict:
        """Extract article content from web page."""
        if not trafilatura and not Article:
            return self._create_error_response(
                "Article processing not available. Install: pip install trafilatura newspaper3k"
            )
        
        try:
            logger.info(f"Extracting article from: {url}")
            
            text = None
            title = None
            author = None
            publish_date = None
            
            # Try trafilatura first
            if trafilatura:
                try:
                    downloaded = trafilatura.fetch_url(url)
                    text = trafilatura.extract(downloaded, include_comments=False)
                    
                    metadata = trafilatura.extract_metadata(downloaded)
                    if metadata:
                        title = metadata.title
                        author = metadata.author
                        publish_date = metadata.date
                except Exception as e:
                    logger.warning(f"Trafilatura failed: {e}")
            
            # Fallback to newspaper3k
            if not text and Article:
                try:
                    article = Article(url)
                    article.download()
                    article.parse()
                    
                    text = article.text
                    title = article.title
                    author = ", ".join(article.authors) if article.authors else None
                    publish_date = str(article.publish_date) if article.publish_date else None
                except Exception as e:
                    logger.warning(f"Newspaper3k failed: {e}")
            
            # Basic scraping fallback
            if not text:
                text = self._basic_article_scrape(url)
            
            if not text:
                return self._create_error_response("Could not extract article content")
            
            return {
                "status": "Success",
                "content_type": "article",
                "transcript": {
                    "text": text,
                    "words": []
                },
                "metadata": {
                    "source_type": "article",
                    "content_length": len(text),
                    "language_code": "en",
                    "url": url,
                    "title": title or "Article",
                    "author": author,
                    "publish_date": publish_date
                },
                "beliefs": beliefs or []
            }
        
        except Exception as e:
            logger.error(f"Article processing error: {e}")
            return self._create_error_response(f"Failed to extract article: {str(e)}")
    
    def _basic_article_scrape(self, url: str) -> str:
        """Basic article scraping fallback."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            paragraphs = soup.find_all('p')
            text = " ".join([p.get_text().strip() for p in paragraphs])
            
            return text.strip()
        
        except Exception as e:
            logger.error(f"Basic scraping error: {e}")
            return ""
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create standardized error response."""
        return {
            "status": "Error",
            "content_type": "invalid",
            "transcript": {
                "text": "",
                "words": []
            },
            "metadata": {
                "source_type": "invalid",
                "content_length": 0,
                "language_code": "en",
                "error": error_message
            },
            "beliefs": []
        }


def transcribe_url(url: str, beliefs: Optional[List] = None) -> Dict:
    """Convenience function to transcribe a URL."""
    transcriber = ContentTranscriber()
    return transcriber.process_url(url, beliefs)
