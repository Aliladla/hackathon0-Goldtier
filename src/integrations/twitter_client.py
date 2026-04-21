"""
Twitter client for Gold tier autonomous AI employee.

Provides Python interface to Twitter API v2 with:
- Tweet creation (single and threads)
- Engagement metrics collection
- Error recovery integration
- Rate limiting
"""

import os
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import tweepy

# Import Gold tier error recovery
try:
    from utils.error_recovery import get_error_recovery, PermanentError
    GOLD_TIER_AVAILABLE = True
except ImportError:
    GOLD_TIER_AVAILABLE = False

logger = logging.getLogger(__name__)


class TwitterClient:
    """Client for Twitter/X integration."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_secret: str,
        bearer_token: str,
        vault_path: Optional[str] = None
    ):
        """
        Initialize Twitter client.

        Args:
            api_key: Twitter API key
            api_secret: Twitter API secret
            access_token: Twitter access token
            access_secret: Twitter access token secret
            bearer_token: Twitter bearer token
            vault_path: Path to vault for storing tweets
        """
        self.vault_path = vault_path

        # Initialize Tweepy client (API v2)
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
            wait_on_rate_limit=True
        )

        # Error recovery
        self.error_recovery = None
        if GOLD_TIER_AVAILABLE:
            try:
                self.error_recovery = get_error_recovery()
            except RuntimeError:
                logger.warning("Error recovery not initialized, using basic error handling")

        logger.info("TwitterClient initialized")

    def _execute_with_recovery(self, func, *args, **kwargs):
        """Execute function with error recovery."""
        if self.error_recovery:
            return self.error_recovery.with_retry(func, *args, **kwargs)
        else:
            return func(*args, **kwargs)

    def create_tweet(
        self,
        text: str,
        reply_to_tweet_id: Optional[str] = None,
        media_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a single tweet.

        Args:
            text: Tweet text (max 280 characters)
            reply_to_tweet_id: Optional tweet ID to reply to
            media_ids: Optional media IDs to attach

        Returns:
            Created tweet details

        Raises:
            Exception: If tweet creation fails
        """
        def _create():
            # Truncate text if needed
            tweet_text = text[:280]

            # Create tweet
            response = self.client.create_tweet(
                text=tweet_text,
                in_reply_to_tweet_id=reply_to_tweet_id,
                media_ids=media_ids
            )

            result = {
                'id': response.data['id'],
                'tweet_id': response.data['id'],
                'text': response.data['text'],
                'created_at': datetime.now().isoformat(),
                'platform': 'twitter',
            }

            logger.info(f"Created tweet: {result['tweet_id']}")
            return result

        try:
            return self._execute_with_recovery(_create)
        except Exception as e:
            # Queue operation if error recovery available
            if self.error_recovery:
                self.error_recovery.queue_operation({
                    'type': 'create_tweet',
                    'text': text,
                    'reply_to_tweet_id': reply_to_tweet_id,
                    'media_ids': media_ids,
                })
                logger.warning(f"Tweet creation queued due to error: {e}")
            raise

    def create_thread(
        self,
        tweets: List[str]
    ) -> Dict[str, Any]:
        """
        Create a tweet thread.

        Args:
            tweets: List of tweet texts (each max 280 characters)

        Returns:
            Thread details with all tweet IDs

        Raises:
            Exception: If thread creation fails
        """
        def _create_thread():
            if not tweets or len(tweets) == 0:
                raise ValueError("Thread must contain at least one tweet")

            created_tweets = []
            previous_tweet_id = None

            for tweet_text in tweets:
                tweet = self.create_tweet(
                    text=tweet_text,
                    reply_to_tweet_id=previous_tweet_id
                )
                created_tweets.append(tweet)
                previous_tweet_id = tweet['tweet_id']

            result = {
                'thread_id': created_tweets[0]['tweet_id'],
                'tweets': created_tweets,
                'count': len(created_tweets),
                'platform': 'twitter',
            }

            logger.info(f"Created tweet thread: {result['thread_id']} ({result['count']} tweets)")
            return result

        return self._execute_with_recovery(_create_thread)

    def get_tweet_metrics(
        self,
        tweet_id: str
    ) -> Dict[str, Any]:
        """
        Get engagement metrics for a tweet.

        Args:
            tweet_id: Twitter tweet ID

        Returns:
            Tweet metrics and engagement data

        Raises:
            Exception: If metrics retrieval fails
        """
        def _get_metrics():
            # Get tweet with metrics
            response = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=['public_metrics', 'created_at', 'text']
            )

            tweet = response.data
            metrics = tweet.public_metrics

            # Calculate engagement rate
            impressions = metrics.get('impression_count', 0)
            engagements = (
                metrics.get('like_count', 0) +
                metrics.get('retweet_count', 0) +
                metrics.get('reply_count', 0)
            )
            engagement_rate = (engagements / impressions * 100) if impressions > 0 else 0

            result = {
                'tweet_id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at.isoformat(),
                'metrics': {
                    'retweets': metrics.get('retweet_count', 0),
                    'replies': metrics.get('reply_count', 0),
                    'likes': metrics.get('like_count', 0),
                    'quotes': metrics.get('quote_count', 0),
                    'impressions': impressions,
                },
                'engagement_rate': round(engagement_rate, 2),
                'platform': 'twitter',
            }

            logger.info(f"Retrieved tweet metrics: {tweet_id}")
            return result

        return self._execute_with_recovery(_get_metrics)

    def delete_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """
        Delete a tweet.

        Args:
            tweet_id: Tweet ID to delete

        Returns:
            Deletion result

        Raises:
            Exception: If deletion fails
        """
        def _delete():
            response = self.client.delete_tweet(id=tweet_id)

            result = {
                'deleted': response.data.get('deleted', False),
                'tweet_id': tweet_id,
                'platform': 'twitter',
            }

            logger.info(f"Deleted tweet: {tweet_id}")
            return result

        return self._execute_with_recovery(_delete)


def create_twitter_client(vault_path: Optional[str] = None) -> Optional[TwitterClient]:
    """
    Create Twitter client from environment variables.

    Args:
        vault_path: Path to vault for storing tweets

    Returns:
        TwitterClient instance or None if not configured
    """
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_secret = os.getenv('TWITTER_ACCESS_SECRET')
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')

    if not all([api_key, api_secret, access_token, access_secret, bearer_token]):
        logger.warning("Twitter not configured (missing environment variables)")
        return None

    return TwitterClient(api_key, api_secret, access_token, access_secret, bearer_token, vault_path)
