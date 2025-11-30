"""
HackerNews API scraper for fetching trending tech topics.
Uses official HackerNews Firebase API: https://hacker-news.firebaseio.com/v0/
"""

import requests
from typing import List, Dict, Optional
import time


def get_trending_hn(limit: int = 10, timeout: int = 5) -> List[Dict]:
    """
    Fetch top trending stories from HackerNews.

    Args:
        limit: Number of stories to fetch (default: 10)
        timeout: Request timeout in seconds (default: 5)

    Returns:
        List of dicts with: {
            "id": story_id,
            "title": story_title,
            "score": upvote_count,
            "url": story_url,
            "by": author,
            "time": unix_timestamp
        }

    Raises:
        requests.RequestException: If API call fails
        TimeoutError: If request exceeds timeout

    Example:
        trending = get_trending_hn(limit=5)
        for story in trending:
            print(f"{story['title']} ({story['score']} points)")
    """

    base_url = "https://hacker-news.firebaseio.com/v0"

    try:
        # Get IDs of top stories
        print(f"Fetching top {limit} HackerNews stories...")
        top_stories_response = requests.get(
            f"{base_url}/topstories.json",
            timeout=timeout
        )
        top_stories_response.raise_for_status()
        top_story_ids = top_stories_response.json()[:limit]

        # Fetch details for each story
        stories = []
        for story_id in top_story_ids:
            try:
                story_response = requests.get(
                    f"{base_url}/item/{story_id}.json",
                    timeout=timeout
                )
                story_response.raise_for_status()
                story = story_response.json()

                # Skip if story is deleted or has no title
                if story is None or "title" not in story:
                    continue

                stories.append({
                    "id": story.get("id"),
                    "title": story.get("title"),
                    "score": story.get("score", 0),
                    "url": story.get("url", ""),
                    "by": story.get("by", "unknown"),
                    "time": story.get("time")
                })

                # Small delay to be respectful to the API
                time.sleep(0.1)

            except requests.RequestException as e:
                print(f"Warning: Failed to fetch story {story_id}: {e}")
                continue

        print(f"✓ Fetched {len(stories)} stories from HackerNews")
        return stories

    except requests.Timeout:
        raise TimeoutError(f"HackerNews API request timed out after {timeout} seconds")
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch HackerNews data: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error fetching HackerNews: {e}")
