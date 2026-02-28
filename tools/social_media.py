import logging
import os
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ===== Optional Dependencies =====
TWITTER_AVAILABLE = False
DISCORD_AVAILABLE = False
REDDIT_AVAILABLE = False

try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    pass

try:
    import praw
    REDDIT_AVAILABLE = True
except ImportError:
    pass


class SocialMediaTool:
    """
    Social media interaction tools for openApex.
    Supports Twitter/X, Discord, Reddit, and Telegram.
    Each platform requires its own API keys set in .env.
    """

    # ===== Twitter/X =====
    
    @staticmethod
    def twitter_post(text: str) -> Dict[str, Any]:
        """Post a tweet."""
        if not TWITTER_AVAILABLE:
            return {"status": "error", "message": "tweepy not installed. Run: pip install tweepy"}
        
        try:
            api_key = os.getenv("TWITTER_API_KEY")
            api_secret = os.getenv("TWITTER_API_SECRET")
            access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            access_secret = os.getenv("TWITTER_ACCESS_SECRET")
            
            if not all([api_key, api_secret, access_token, access_secret]):
                return {"status": "error", "message": "Twitter API keys not set in .env"}
            
            client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret
            )
            
            # Truncate to 280 chars
            if len(text) > 280:
                text = text[:277] + "..."
            
            response = client.create_tweet(text=text)
            tweet_id = response.data['id']
            
            logger.info(f"[Twitter] Posted tweet: {tweet_id}")
            return {
                "status": "success",
                "platform": "twitter",
                "tweet_id": str(tweet_id),
                "text": text
            }
        except Exception as e:
            logger.error(f"[Twitter] Post error: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def twitter_search(query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search recent tweets."""
        if not TWITTER_AVAILABLE:
            return {"status": "error", "message": "tweepy not installed"}
        
        try:
            bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
            if not bearer_token:
                return {"status": "error", "message": "TWITTER_BEARER_TOKEN not set"}
            
            client = tweepy.Client(bearer_token=bearer_token)
            tweets = client.search_recent_tweets(query=query, max_results=min(max_results, 10))
            
            results = []
            if tweets.data:
                for tweet in tweets.data:
                    results.append({"id": str(tweet.id), "text": tweet.text})
            
            return {"status": "success", "platform": "twitter", "results": results, "count": len(results)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def twitter_reply(tweet_id: str, text: str) -> Dict[str, Any]:
        """Reply to a tweet."""
        if not TWITTER_AVAILABLE:
            return {"status": "error", "message": "tweepy not installed"}
        
        try:
            api_key = os.getenv("TWITTER_API_KEY")
            api_secret = os.getenv("TWITTER_API_SECRET")
            access_token = os.getenv("TWITTER_ACCESS_TOKEN")
            access_secret = os.getenv("TWITTER_ACCESS_SECRET")
            
            if not all([api_key, api_secret, access_token, access_secret]):
                return {"status": "error", "message": "Twitter API keys not set"}
            
            client = tweepy.Client(
                consumer_key=api_key, consumer_secret=api_secret,
                access_token=access_token, access_token_secret=access_secret
            )
            
            if len(text) > 280:
                text = text[:277] + "..."
            
            response = client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
            return {"status": "success", "platform": "twitter", "reply_id": str(response.data['id'])}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ===== Reddit =====

    @staticmethod
    def reddit_post(subreddit: str, title: str, body: str) -> Dict[str, Any]:
        """Post to a subreddit."""
        if not REDDIT_AVAILABLE:
            return {"status": "error", "message": "praw not installed. Run: pip install praw"}
        
        try:
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                username=os.getenv("REDDIT_USERNAME"),
                password=os.getenv("REDDIT_PASSWORD"),
                user_agent="openApex/4.0"
            )
            
            sub = reddit.subreddit(subreddit)
            submission = sub.submit(title=title, selftext=body)
            
            logger.info(f"[Reddit] Posted to r/{subreddit}: {submission.id}")
            return {"status": "success", "platform": "reddit", "post_id": str(submission.id), "url": submission.url}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def reddit_read(subreddit: str, limit: int = 5, sort: str = "hot") -> Dict[str, Any]:
        """Read posts from a subreddit."""
        if not REDDIT_AVAILABLE:
            return {"status": "error", "message": "praw not installed"}
        
        try:
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent="openApex/4.0"
            )
            
            sub = reddit.subreddit(subreddit)
            posts = []
            
            if sort == "new":
                submissions = sub.new(limit=limit)
            elif sort == "top":
                submissions = sub.top(limit=limit)
            else:
                submissions = sub.hot(limit=limit)
            
            for post in submissions:
                posts.append({
                    "id": post.id,
                    "title": post.title,
                    "score": post.score,
                    "url": post.url,
                    "text": post.selftext[:200] if post.selftext else ""
                })
            
            return {"status": "success", "platform": "reddit", "subreddit": subreddit, "posts": posts}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def reddit_comment(post_id: str, text: str) -> Dict[str, Any]:
        """Comment on a Reddit post."""
        if not REDDIT_AVAILABLE:
            return {"status": "error", "message": "praw not installed"}
        
        try:
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                username=os.getenv("REDDIT_USERNAME"),
                password=os.getenv("REDDIT_PASSWORD"),
                user_agent="openApex/4.0"
            )
            
            submission = reddit.submission(id=post_id)
            comment = submission.reply(text)
            
            return {"status": "success", "platform": "reddit", "comment_id": str(comment.id)}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# ===== JSON Schemas =====

SOCIAL_POST_SCHEMA = {
    "type": "function",
    "function": {
        "name": "social_post",
        "description": "Post content to social media. Supports Twitter/X and Reddit.",
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "'twitter' or 'reddit'"},
                "text": {"type": "string", "description": "Content to post (Twitter: max 280 chars)"},
                "subreddit": {"type": "string", "description": "For Reddit: target subreddit name"},
                "title": {"type": "string", "description": "For Reddit: post title"}
            },
            "required": ["platform", "text"]
        }
    }
}

SOCIAL_READ_SCHEMA = {
    "type": "function",
    "function": {
        "name": "social_read",
        "description": "Read/search content from social media platforms.",
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "'twitter' or 'reddit'"},
                "query": {"type": "string", "description": "Search query (Twitter) or subreddit name (Reddit)"},
                "limit": {"type": "integer", "description": "Max results. Default: 5"}
            },
            "required": ["platform", "query"]
        }
    }
}

SOCIAL_REPLY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "social_reply",
        "description": "Reply/comment on a social media post.",
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "description": "'twitter' or 'reddit'"},
                "post_id": {"type": "string", "description": "ID of the post to reply to"},
                "text": {"type": "string", "description": "Reply text"}
            },
            "required": ["platform", "post_id", "text"]
        }
    }
}
