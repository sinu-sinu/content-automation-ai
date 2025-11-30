"""
Tech Scout Agent: Research trending tech topics and compile research briefs.

Capabilities:
- Auto-discover trending topics from HackerNews
- Research topics with context for specific YouTube channels
- Select the best trending topic for content creation
- Comprehensive demo mode with fallback system
"""

from typing import Dict, List, Optional
from src.utils.openai_client import OpenAIClient
from src.utils.hn_scraper import get_trending_hn
from src.utils.brand_voice_loader import load_brand_voice
import json
import os
import threading


class TechScoutAgent:
    """Tech Scout Agent for researching and evaluating trending tech topics."""

    def __init__(self, openai_client: OpenAIClient, channel_name: str = "Fireship", demo_mode: bool = False):
        """
        Initialize Tech Scout Agent.

        Args:
            openai_client: OpenAIClient instance for API calls
            channel_name: Name of the YouTube channel (for flexible multi-channel support)
            demo_mode: If True, use cached data instead of live API
        """
        self.client = openai_client
        self.channel_name = channel_name
        self.demo_mode = demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"

        # Load brand voice profile from config folder
        try:
            self.brand_voice = load_brand_voice(channel_name)
        except (FileNotFoundError, ValueError):
            print(f"WARNING: Brand voice config not found for {channel_name}, using generic mode")
            self.brand_voice = None

        # System prompt uses brand voice profile (or generic if not available)
        self.system_prompt = self._create_system_prompt(self.brand_voice)

    def _create_system_prompt(self, brand_voice: Optional[Dict] = None) -> str:
        """
        Create system prompt for Fireship tech scouting using brand voice profile.

        Args:
            brand_voice: Brand voice profile dict loaded from config

        Returns:
            System prompt for tech scouting, customized to Fireship's voice
        """
        # Extract brand voice characteristics for Fireship
        tone = ", ".join(brand_voice.get("tone", ["sarcastic", "deadpan"])) if brand_voice else "sarcastic, deadpan"
        humor_types = ", ".join(brand_voice.get("humor_types", []) if brand_voice else ["programming memes", "tech culture references"])
        signature_phrases = ", ".join(brand_voice.get("signature_phrases", [])[:3] if brand_voice else ["like and subscribe", "it's actually pretty simple"])

        return f"""You are a tech trend scout for Fireship,
        a fast-paced programming YouTube channel. Your job is to find
        interesting, meme-worthy tech topics that programmers will love.

        Brand Voice: {tone}
        Humor Style: {humor_types}
        Signature Phrases: {signature_phrases}

        Prioritize:
        - Breaking news (new framework releases, tech drama, AI breakthroughs)
        - Controversial takes (tabs vs spaces, framework wars)
        - Absurd tech trends (yet another JS framework)
        - Developer pain points (bugs, deprecations, breaking changes)

        Format your research brief with:
        1. Topic summary (2-3 sentences)
        2. Why it's interesting for developers
        3. Key talking points (3-5 bullet points)
        4. Meme potential (1-10 score)
        5. Suggested angle (hot take or educational)
        6. Relevant code examples or tools mentioned"""

    def research_topic(self, topic: Optional[str] = None) -> Dict:
        """
        Research a topic or auto-discover trending topics.

        If no topic provided, automatically discovers and selects best trending topic
        from HackerNews (with fallback to cached data for reliability).

        Args:
            topic: Specific topic to research. If None, auto-discover trending.

        Returns:
            Dictionary with:
            {
                "topic": str,
                "brief": str (formatted research brief),
                "sources": list of source URLs,
                "mode": str ("live" or "cached")
            }
        """
        mode = "live"

        # Auto-discover trending topic if not provided
        if not topic:
            print(f"[SCOUT] Auto-discovering trending topics for {self.channel_name}...")
            trending = self._get_trending_safe()
            if self.demo_mode or isinstance(trending, list) and len(trending) > 0:
                mode = "cached" if self.demo_mode else "live"
            topic = self._select_best_topic(trending)
            print(f"[SCOUT] Selected topic: {topic}")

        # Research the topic using OpenAI
        print(f"[SCOUT] Researching '{topic}'...")
        user_message = f"""Research this topic for a {self.channel_name} video: {topic}

        Provide:
        - Core concept explanation (what is this?)
        - Why developers should care
        - Controversial or funny angles
        - Key technical details
        - Meme opportunities or visual ideas
        - Similar or related topics"""

        brief = self.client.call_agent(
            agent_type="scout",
            system_prompt=self.system_prompt,
            user_message=user_message,
            max_tokens=2048
        )

        print("[SCOUT] Research complete")

        return {
            "topic": topic,
            "brief": brief,
            "sources": [],  # Would add real sources in production
            "mode": mode
        }

    def _get_trending_safe(self) -> List[Dict]:
        """
        Get trending topics with automatic fallback to cached data.

        Behavior:
        - DEMO_MODE=true: Uses cached data immediately
        - DEMO_MODE=false: Tries live API with 5-second timeout
        - On timeout/error: Falls back to cached data
        - On missing cache: Falls back to hardcoded topics

        Cross-platform: Uses threading (works on Windows, Mac, Linux)

        Returns:
            List of trending items with id, title, score, url fields
        """
        if self.demo_mode:
            print("[SCOUT] DEMO MODE: Using cached trending topics")
            return self._load_cached_trends()

        try:
            # Use threading for cross-platform timeout support
            result = [None]  # Mutable container for thread result
            error = [None]

            def scrape_with_timeout():
                try:
                    result[0] = get_trending_hn(limit=10)
                except Exception as e:
                    error[0] = e

            thread = threading.Thread(target=scrape_with_timeout, daemon=True)
            thread.start()
            thread.join(timeout=5.0)  # 5-second timeout

            # Check if thread finished
            if thread.is_alive():
                print("[SCOUT] HackerNews API timeout (>5s), using cached data")
                return self._load_cached_trends()

            # Check for errors
            if error[0]:
                print(f"[SCOUT] HackerNews API error: {error[0]}, using cached data")
                return self._load_cached_trends()

            # Check if we got results
            if not result[0]:
                print("[SCOUT] No results from HackerNews, using cached data")
                return self._load_cached_trends()

            print("[SCOUT] Using live HackerNews data")
            return result[0]

        except Exception as e:
            print(f"[SCOUT] Unexpected error: {e}, using cached data")
            return self._load_cached_trends()

    def _load_cached_trends(self) -> List[Dict]:
        """
        Load pre-saved trending topics for demo reliability.

        Requires: examples/cached_hn_trending.json

        Returns:
            List of cached trending items

        Raises:
            FileNotFoundError: If cache file is missing
            ValueError: If cache JSON is invalid
        """
        # Find cache file relative to project root
        import pathlib
        project_root = pathlib.Path(__file__).parent.parent.parent
        cache_file = project_root / "examples" / "cached_hn_trending.json"

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                print(f"[SCOUT] Loaded {len(data)} cached trends")
                return data
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Cache file required: {cache_file}\n"
                f"Please ensure examples/cached_hn_trending.json exists with trending topics."
            ) from e
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in cache file ({cache_file}): {e}"
            ) from e

    def _select_best_topic(self, trending_items: List[Dict]) -> str:
        """
        Use LLM to pick the most suitable topic for Fireship.

        Considers:
        - Developer relevance
        - Meme potential
        - Timing (breaking news vs evergreen)
        - Controversy level
        - Fireship suitability

        Args:
            trending_items: List of trending items with title and score

        Returns:
            Selected topic title as string
        """
        if not trending_items:
            return "The Latest JavaScript Framework Nobody Asked For"

        # Format topics for LLM
        topics_str = "\n".join([
            f"{i+1}. {item['title']} (score: {item.get('score', 'N/A')})"
            for i, item in enumerate(trending_items[:10])  # Top 10
        ])

        prompt = f"""From these trending tech topics, pick the ONE
        that would make the best Fireship video. Consider:
        - Developer relevance and interest
        - Meme potential or humor angle
        - Timing (is it breaking news or timeless?)
        - Controversy level (if appropriate)
        - How well it aligns with Fireship's sarcastic, meme-heavy style

        Topics:
        {topics_str}

        Respond with ONLY the topic title (exactly as written above), nothing else."""

        response = self.client.call_agent(
            agent_type="scout",
            system_prompt="You are a topic selector for Fireship. Pick topics that align with sarcastic humor, developer pain points, and tech culture.",
            user_message=prompt,
            temperature=0.3,
            max_tokens=100
        )

        return response.strip()
