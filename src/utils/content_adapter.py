"""
Content adapter for Gold tier autonomous AI employee.

Adapts business updates to platform-specific formats:
- Facebook: Detailed posts with full context
- Instagram: Visual-focused with hashtags (2200 char limit)
- Twitter: Concise with thread support (280 char limit)
"""

import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class ContentAdapter:
    """Adapts content for different social media platforms."""

    def __init__(self):
        """Initialize content adapter."""
        self.facebook_max_length = 63206  # Facebook post limit
        self.instagram_max_length = 2200  # Instagram caption limit
        self.twitter_max_length = 280  # Twitter tweet limit

    def adapt_for_facebook(
        self,
        content: str,
        title: Optional[str] = None,
        link: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Adapt content for Facebook (detailed posts).

        Args:
            content: Original content
            title: Optional title
            link: Optional link to include

        Returns:
            Adapted content for Facebook
        """
        # Facebook allows detailed posts
        adapted = ""

        if title:
            adapted += f"**{title}**\n\n"

        adapted += content

        if link:
            adapted += f"\n\n🔗 {link}"

        # Add call to action
        adapted += "\n\n💬 What do you think? Let us know in the comments!"

        # Truncate if needed (rare)
        if len(adapted) > self.facebook_max_length:
            adapted = adapted[:self.facebook_max_length - 3] + "..."

        logger.debug(f"Adapted content for Facebook: {len(adapted)} chars")

        return {
            'message': adapted,
            'link': link,
            'platform': 'facebook',
        }

    def adapt_for_instagram(
        self,
        content: str,
        title: Optional[str] = None,
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Adapt content for Instagram (visual + hashtags, 2200 char limit).

        Args:
            content: Original content
            title: Optional title
            hashtags: Optional list of hashtags

        Returns:
            Adapted content for Instagram
        """
        adapted = ""

        if title:
            adapted += f"{title}\n\n"

        # Instagram is visual-first, so keep text concise
        # Extract key points
        sentences = content.split('.')
        key_points = []
        char_count = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and char_count + len(sentence) < 1500:  # Leave room for hashtags
                key_points.append(sentence)
                char_count += len(sentence)

        adapted += '. '.join(key_points)
        if key_points:
            adapted += '.'

        # Add emojis for visual appeal
        adapted = self._add_emojis(adapted)

        # Add hashtags
        if hashtags:
            adapted += "\n\n"
            for tag in hashtags[:30]:  # Instagram allows up to 30 hashtags
                if not tag.startswith('#'):
                    tag = f"#{tag}"
                adapted += f"{tag} "
        else:
            # Generate default hashtags
            adapted += "\n\n#business #update #news #entrepreneur #success"

        # Truncate to Instagram limit
        if len(adapted) > self.instagram_max_length:
            adapted = adapted[:self.instagram_max_length - 3] + "..."

        logger.debug(f"Adapted content for Instagram: {len(adapted)} chars")

        return {
            'caption': adapted,
            'platform': 'instagram',
        }

    def adapt_for_twitter(
        self,
        content: str,
        title: Optional[str] = None,
        link: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Adapt content for Twitter (concise, 280 char limit, thread support).

        Args:
            content: Original content
            title: Optional title
            link: Optional link to include

        Returns:
            Adapted content for Twitter (single tweet or thread)
        """
        # Check if content fits in single tweet
        single_tweet = self._create_single_tweet(content, title, link)

        if len(single_tweet) <= self.twitter_max_length:
            logger.debug(f"Adapted content for Twitter: single tweet ({len(single_tweet)} chars)")
            return {
                'text': single_tweet,
                'is_thread': False,
                'platform': 'twitter',
            }

        # Content too long, create thread
        thread = self._create_thread(content, title, link)

        logger.debug(f"Adapted content for Twitter: thread ({len(thread)} tweets)")

        return {
            'tweets': thread,
            'is_thread': True,
            'platform': 'twitter',
        }

    def _create_single_tweet(
        self,
        content: str,
        title: Optional[str] = None,
        link: Optional[str] = None
    ) -> str:
        """Create a single tweet."""
        tweet = ""

        if title:
            tweet += f"{title}: "

        # Extract first sentence or key point
        first_sentence = content.split('.')[0].strip()
        tweet += first_sentence

        if link:
            # Reserve space for link (23 chars for t.co)
            available_space = self.twitter_max_length - len(tweet) - 24
            if available_space > 0:
                tweet += f"\n\n{link}"

        return tweet

    def _create_thread(
        self,
        content: str,
        title: Optional[str] = None,
        link: Optional[str] = None
    ) -> List[str]:
        """Create a tweet thread."""
        tweets = []

        # First tweet: Title + hook
        first_tweet = ""
        if title:
            first_tweet = f"{title}\n\n🧵 Thread 👇"
        else:
            first_tweet = f"{content.split('.')[0].strip()}...\n\n🧵 Thread 👇"

        tweets.append(first_tweet[:self.twitter_max_length])

        # Split content into sentences
        sentences = [s.strip() + '.' for s in content.split('.') if s.strip()]

        # Group sentences into tweets
        current_tweet = ""
        tweet_number = 2

        for sentence in sentences:
            # Check if adding this sentence would exceed limit
            test_tweet = current_tweet + " " + sentence if current_tweet else sentence
            test_tweet = f"{tweet_number}/ {test_tweet}"

            if len(test_tweet) <= self.twitter_max_length:
                current_tweet = current_tweet + " " + sentence if current_tweet else sentence
            else:
                # Save current tweet and start new one
                if current_tweet:
                    tweets.append(f"{tweet_number}/ {current_tweet}")
                    tweet_number += 1
                current_tweet = sentence

        # Add remaining content
        if current_tweet:
            tweets.append(f"{tweet_number}/ {current_tweet}")

        # Add link to last tweet if provided
        if link:
            last_tweet = tweets[-1]
            if len(last_tweet) + len(link) + 2 <= self.twitter_max_length:
                tweets[-1] = f"{last_tweet}\n\n{link}"
            else:
                tweets.append(f"{tweet_number + 1}/ {link}")

        return tweets

    def _add_emojis(self, text: str) -> str:
        """Add relevant emojis to text for Instagram."""
        # Simple emoji mapping
        emoji_map = {
            'announce': '📢',
            'launch': '🚀',
            'new': '✨',
            'success': '🎉',
            'grow': '📈',
            'team': '👥',
            'product': '💼',
            'service': '🛠️',
            'update': '🔄',
            'improve': '⬆️',
        }

        text_lower = text.lower()
        for keyword, emoji in emoji_map.items():
            if keyword in text_lower and emoji not in text:
                # Add emoji at the beginning
                text = f"{emoji} {text}"
                break

        return text

    def adapt_business_update(
        self,
        content: str,
        title: Optional[str] = None,
        link: Optional[str] = None,
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Adapt business update for all platforms.

        Args:
            content: Original content
            title: Optional title
            link: Optional link
            hashtags: Optional hashtags for Instagram

        Returns:
            Dict with adapted content for each platform
        """
        return {
            'facebook': self.adapt_for_facebook(content, title, link),
            'instagram': self.adapt_for_instagram(content, title, hashtags),
            'twitter': self.adapt_for_twitter(content, title, link),
        }


def create_content_adapter() -> ContentAdapter:
    """
    Create content adapter instance.

    Returns:
        ContentAdapter instance
    """
    return ContentAdapter()
