"""
Facebook client for Gold tier autonomous AI employee.

Provides Python interface to Facebook Graph API with:
- Post creation (text, link, image)
- Engagement metrics collection
- Error recovery integration
- Rate limiting
"""

import os
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
import facebook

# Import Gold tier error recovery
try:
    from utils.error_recovery import get_error_recovery, PermanentError
    GOLD_TIER_AVAILABLE = True
except ImportError:
    GOLD_TIER_AVAILABLE = False

logger = logging.getLogger(__name__)


class FacebookClient:
    """Client for Facebook integration."""

    def __init__(
        self,
        page_access_token: str,
        page_id: str,
        vault_path: Optional[str] = None
    ):
        """
        Initialize Facebook client.

        Args:
            page_access_token: Facebook Page access token
            page_id: Facebook Page ID
            vault_path: Path to vault for storing posts
        """
        self.page_access_token = page_access_token
        self.page_id = page_id
        self.vault_path = vault_path
        self.graph = facebook.GraphAPI(access_token=page_access_token, version='3.1')

        # Error recovery
        self.error_recovery = None
        if GOLD_TIER_AVAILABLE:
            try:
                self.error_recovery = get_error_recovery()
            except RuntimeError:
                logger.warning("Error recovery not initialized, using basic error handling")

        logger.info(f"FacebookClient initialized for page {page_id}")

    def _execute_with_recovery(self, func, *args, **kwargs):
        """Execute function with error recovery."""
        if self.error_recovery:
            return self.error_recovery.with_retry(func, *args, **kwargs)
        else:
            return func(*args, **kwargs)

    def create_post(
        self,
        message: str,
        link: Optional[str] = None,
        image_url: Optional[str] = None,
        scheduled_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create Facebook post.

        Args:
            message: Post message/content
            link: Optional link to share
            image_url: Optional image URL
            scheduled_time: Optional Unix timestamp for scheduled post

        Returns:
            Created post details

        Raises:
            Exception: If post creation fails
        """
        def _create():
            params = {'message': message}

            if link:
                params['link'] = link

            if image_url:
                params['url'] = image_url

            if scheduled_time:
                params['published'] = False
                params['scheduled_publish_time'] = scheduled_time

            response = self.graph.put_object(
                parent_object=self.page_id,
                connection_name='feed',
                **params
            )

            result = {
                'id': response['id'],
                'post_id': response['id'],
                'message': message,
                'created_time': datetime.now().isoformat(),
                'scheduled': bool(scheduled_time),
                'platform': 'facebook',
            }

            logger.info(f"Created Facebook post: {result['post_id']}")
            return result

        try:
            return self._execute_with_recovery(_create)
        except Exception as e:
            # Queue operation if error recovery available
            if self.error_recovery:
                self.error_recovery.queue_operation({
                    'type': 'create_facebook_post',
                    'message': message,
                    'link': link,
                    'image_url': image_url,
                    'scheduled_time': scheduled_time,
                })
                logger.warning(f"Facebook post creation queued due to error: {e}")
            raise

    def get_post_insights(
        self,
        post_id: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get engagement metrics for a post.

        Args:
            post_id: Facebook post ID
            metrics: Optional list of specific metrics

        Returns:
            Post insights and engagement data

        Raises:
            Exception: If insights retrieval fails
        """
        def _get_insights():
            # Default metrics
            if not metrics:
                metrics_to_fetch = [
                    'post_impressions',
                    'post_impressions_unique',
                    'post_engaged_users',
                    'post_clicks',
                    'post_reactions_like_total',
                ]
            else:
                metrics_to_fetch = metrics

            # Get insights
            insights_response = self.graph.get_object(
                id=f"{post_id}/insights",
                metric=','.join(metrics_to_fetch)
            )

            # Parse insights
            insights = {}
            if 'data' in insights_response:
                for metric in insights_response['data']:
                    insights[metric['name']] = metric['values'][0]['value'] if metric['values'] else 0

            # Get post details
            post_response = self.graph.get_object(
                id=post_id,
                fields='message,created_time,shares,comments.summary(true),reactions.summary(true)'
            )

            result = {
                'post_id': post_id,
                'message': post_response.get('message', ''),
                'created_time': post_response.get('created_time', ''),
                'insights': insights,
                'engagement': {
                    'shares': post_response.get('shares', {}).get('count', 0),
                    'comments': post_response.get('comments', {}).get('summary', {}).get('total_count', 0),
                    'reactions': post_response.get('reactions', {}).get('summary', {}).get('total_count', 0),
                },
                'platform': 'facebook',
            }

            logger.info(f"Retrieved Facebook post insights: {post_id}")
            return result

        return self._execute_with_recovery(_get_insights)

    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """
        Delete a Facebook post.

        Args:
            post_id: Post ID to delete

        Returns:
            Deletion result

        Raises:
            Exception: If deletion fails
        """
        def _delete():
            response = self.graph.delete_object(id=post_id)

            result = {
                'success': response.get('success', False),
                'post_id': post_id,
                'platform': 'facebook',
            }

            logger.info(f"Deleted Facebook post: {post_id}")
            return result

        return self._execute_with_recovery(_delete)


def create_facebook_client(vault_path: Optional[str] = None) -> Optional[FacebookClient]:
    """
    Create Facebook client from environment variables.

    Args:
        vault_path: Path to vault for storing posts

    Returns:
        FacebookClient instance or None if not configured
    """
    page_access_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
    page_id = os.getenv('FACEBOOK_PAGE_ID')

    if not all([page_access_token, page_id]):
        logger.warning("Facebook not configured (missing environment variables)")
        return None

    return FacebookClient(page_access_token, page_id, vault_path)
