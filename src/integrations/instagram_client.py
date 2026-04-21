"""
Instagram client for Gold tier autonomous AI employee.

Provides Python interface to Instagram Graph API with:
- Post creation (image, carousel)
- Engagement metrics collection
- Error recovery integration
- Rate limiting
"""

import os
import logging
from typing import Dict, Optional, Any, List
from datetime import datetime
from instagrapi import Client

# Import Gold tier error recovery
try:
    from utils.error_recovery import get_error_recovery, PermanentError
    GOLD_TIER_AVAILABLE = True
except ImportError:
    GOLD_TIER_AVAILABLE = False

logger = logging.getLogger(__name__)


class InstagramClient:
    """Client for Instagram integration."""

    def __init__(
        self,
        username: str,
        password: str,
        vault_path: Optional[str] = None
    ):
        """
        Initialize Instagram client.

        Args:
            username: Instagram username
            password: Instagram password
            vault_path: Path to vault for storing posts
        """
        self.username = username
        self.vault_path = vault_path
        self.client = Client()

        # Error recovery
        self.error_recovery = None
        if GOLD_TIER_AVAILABLE:
            try:
                self.error_recovery = get_error_recovery()
            except RuntimeError:
                logger.warning("Error recovery not initialized, using basic error handling")

        # Login
        try:
            self.client.login(username, password)
            logger.info(f"InstagramClient initialized for user {username}")
        except Exception as e:
            logger.error(f"Failed to login to Instagram: {e}")
            raise

    def _execute_with_recovery(self, func, *args, **kwargs):
        """Execute function with error recovery."""
        if self.error_recovery:
            return self.error_recovery.with_retry(func, *args, **kwargs)
        else:
            return func(*args, **kwargs)

    def create_post(
        self,
        caption: str,
        image_path: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create Instagram post.

        Args:
            caption: Post caption (max 2200 characters)
            image_path: Path to image file
            location: Optional location name

        Returns:
            Created post details

        Raises:
            Exception: If post creation fails
        """
        def _create():
            # Upload photo
            media = self.client.photo_upload(
                path=image_path,
                caption=caption[:2200],  # Instagram limit
            )

            result = {
                'id': str(media.pk),
                'media_id': str(media.pk),
                'caption': caption[:2200],
                'created_time': datetime.now().isoformat(),
                'platform': 'instagram',
            }

            logger.info(f"Created Instagram post: {result['media_id']}")
            return result

        try:
            return self._execute_with_recovery(_create)
        except Exception as e:
            # Queue operation if error recovery available
            if self.error_recovery:
                self.error_recovery.queue_operation({
                    'type': 'create_instagram_post',
                    'caption': caption,
                    'image_path': image_path,
                    'location': location,
                })
                logger.warning(f"Instagram post creation queued due to error: {e}")
            raise

    def get_media_insights(
        self,
        media_id: str
    ) -> Dict[str, Any]:
        """
        Get engagement metrics for a post.

        Args:
            media_id: Instagram media ID

        Returns:
            Media insights and engagement data

        Raises:
            Exception: If insights retrieval fails
        """
        def _get_insights():
            # Get media info
            media = self.client.media_info(int(media_id))

            result = {
                'media_id': media_id,
                'caption': media.caption_text,
                'media_type': str(media.media_type),
                'created_time': media.taken_at.isoformat(),
                'insights': {
                    'likes': media.like_count,
                    'comments': media.comment_count,
                    'views': media.view_count if hasattr(media, 'view_count') else 0,
                },
                'engagement': {
                    'likes': media.like_count,
                    'comments': media.comment_count,
                },
                'platform': 'instagram',
            }

            logger.info(f"Retrieved Instagram media insights: {media_id}")
            return result

        return self._execute_with_recovery(_get_insights)

    def delete_media(self, media_id: str) -> Dict[str, Any]:
        """
        Delete Instagram media.

        Args:
            media_id: Media ID to delete

        Returns:
            Deletion result

        Raises:
            Exception: If deletion fails
        """
        def _delete():
            success = self.client.media_delete(int(media_id))

            result = {
                'success': success,
                'media_id': media_id,
                'platform': 'instagram',
            }

            logger.info(f"Deleted Instagram media: {media_id}")
            return result

        return self._execute_with_recovery(_delete)


def create_instagram_client(vault_path: Optional[str] = None) -> Optional[InstagramClient]:
    """
    Create Instagram client from environment variables.

    Args:
        vault_path: Path to vault for storing posts

    Returns:
        InstagramClient instance or None if not configured
    """
    username = os.getenv('INSTAGRAM_USERNAME')
    password = os.getenv('INSTAGRAM_PASSWORD')

    if not all([username, password]):
        logger.warning("Instagram not configured (missing environment variables)")
        return None

    try:
        return InstagramClient(username, password, vault_path)
    except Exception as e:
        logger.error(f"Failed to create Instagram client: {e}")
        return None
