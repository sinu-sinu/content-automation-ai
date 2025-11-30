"""
Script Writer Agent: Generate Fireship-style scripts with few-shot prompting.

Capabilities:
- Generate channel-specific scripts using few-shot learning
- Support multiple formats (100_seconds, code_report, tutorial)
- Prevent "cringe AI humor" using real examples from brand voice profile
- Flexible for any Electrify channel with different brand profiles
"""

from typing import Dict, Optional
from src.utils.openai_client import OpenAIClient
from src.utils.brand_voice_loader import load_brand_voice
import os


class ScriptWriterAgent:
    """Script Writer Agent for generating channel-specific scripts with few-shot learning."""

    def __init__(self, openai_client: OpenAIClient, channel_name: str = "Fireship", demo_mode: bool = False):
        """
        Initialize Script Writer Agent.

        Args:
            openai_client: OpenAIClient instance for API calls
            channel_name: Name of the YouTube channel (for flexible multi-channel support)
            demo_mode: If True, use demo mode settings
        """
        self.client = openai_client
        self.channel_name = channel_name
        self.demo_mode = demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"

        # Load brand voice profile from config folder
        try:
            self.brand_voice = load_brand_voice(channel_name)
        except (FileNotFoundError, ValueError):
            print(f" Brand voice config not found for {channel_name}, using generic mode")
            self.brand_voice = None

        # System prompt uses brand voice profile (or generic if not available)
        self.system_prompt = self._build_system_prompt(self.brand_voice)

    def _build_system_prompt(self, brand_voice: Optional[Dict] = None) -> str:
        """
        Build system prompt with few-shot examples from brand voice profile.

        This uses REAL examples instead of descriptions to prevent "cringe AI humor".

        Args:
            brand_voice: Brand voice profile dict loaded from config

        Returns:
            System prompt for script writing with few-shot examples
        """
        # Extract brand voice characteristics
        if brand_voice:
            tone = ", ".join(brand_voice.get("tone", ["sarcastic", "deadpan"]))
            pacing = brand_voice.get("pacing", "rapid-fire")
            sentence_length = brand_voice.get("sentence_structure", {}).get("avg_length_words", 10)
            signature_phrases = ", ".join(brand_voice.get("signature_phrases", [])[:3])
            avoid_items = ", ".join(brand_voice.get("avoid", [])[:3])
        else:
            tone = "sarcastic, deadpan"
            pacing = "rapid-fire"
            sentence_length = 10
            signature_phrases = "like and subscribe, it's actually pretty simple, but here's the thing"
            avoid_items = "lengthy explanations, overly formal language, excessive enthusiasm"

        # Build the system prompt with few-shot examples for Fireship
        prompt = f"""You are a scriptwriter for {self.channel_name}, a fast-paced programming YouTube channel.

        CRITICAL: Study these REAL {self.channel_name} examples to understand the tone and rhythm.
        These are NOT descriptions - they are actual script excerpts you MUST mimic:

        EXAMPLE 1 (React Server Components):
        "React Server Components. They're like regular React components, except they run on the server.
        Groundbreaking, I know. But here's the thing - they might actually change how we build web apps forever.
        Or they'll be forgotten in 6 months like Suspense. Let's find out."

        EXAMPLE 2 (TypeScript):
        "TypeScript. It's JavaScript, but with types. Which is great, until you spend 3 hours debugging a
        type error that doesn't exist at runtime. But at least your IDE autocomplete works now."

        EXAMPLE 3 (Docker):
        "Docker. It's like a virtual machine, but lighter. Package your app in a container, ship it anywhere.
        It works on my machine? Now it works on everyone's machine. Unless you forget to expose a port.
        Then it works nowhere."

        VOICE CHARACTERISTICS:
        - Tone: {tone}
        - Pacing: {pacing}
        - Sentence length: ~{sentence_length} words (short and punchy)
        - Pattern: State the obvious → Undercut it with sarcasm/reality → Add a twist or prediction

        SIGNATURE PHRASES (use sparingly and naturally):
        {signature_phrases}

        AVOID AT ALL COSTS:
        {avoid_items}

        CRITICAL INSTRUCTIONS:
        1. Mimic the TIMING and SENTENCE STRUCTURE from examples, not just the words
        2. The humor comes from the rhythm and pacing, not forced jokes
        3. Use short, declarative sentences
        4. Undercut confidence with reality checks
        5. Include code examples with sarcastic inline comments
        6. Include B-ROLL SUGGESTIONS for visuals
        7. Keep energy high and pacing fast"""

        return prompt

    def generate_script(
        self,
        research_brief: str,
        format_type: str = "100_seconds"
    ) -> str:
        """
        Generate a channel-specific script using few-shot learning.

        Args:
            research_brief: Research brief containing topic info and key points
            format_type: Script format - "100_seconds", "code_report", or "tutorial"

        Returns:
            Complete formatted script as string
        """
        if format_type == "100_seconds":
            template = self._get_100s_template()
        elif format_type == "code_report":
            template = self._get_code_report_template()
        elif format_type == "tutorial":
            template = self._get_tutorial_template()
        else:
            template = self._get_100s_template()  # Default to 100 seconds

        user_message = f"""Write a {self.channel_name} script using this research:

        RESEARCH BRIEF:
        {research_brief}

        FORMAT: {format_type}
        TEMPLATE STRUCTURE:
        {template}

        CRITICAL INSTRUCTIONS:
        1. Follow the template structure with exact timestamps
        2. Study the voice examples from your system prompt - mimic that exact pattern:
        - State something obvious in a deadpan way
        - Undercut it with sarcasm or reality check
        - Add a twist, prediction, or joke
        3. Keep sentences short (8-15 words average)
        4. Include code examples where relevant
        5. Make the B-ROLL SUGGESTIONS section specific and actionable
        6. Make it feel like {self.channel_name}, not a generic AI script

        Write the COMPLETE script now:"""

        script = self.client.call_agent(
            agent_type="writer",
            system_prompt=self.system_prompt,
            user_message=user_message,
            model="gpt-4o",  # Use best model for creative writing
            temperature=0.8,
            max_tokens=6000
        )

        return script

    def _get_100s_template(self) -> str:
        """
        Template for 100-second YouTube shorts format.

        Paces to exactly 100 seconds with clear section breaks.
        """
        return """
        [0:00-0:05] HOOK (5 seconds)
        - State something obvious in deadpan way
        - Grab attention immediately
        - Single punchy sentence

        [0:05-0:20] SETUP (15 seconds)
        - What is this thing?
        - Why should you care?
        - Add light sarcasm here

        [0:20-1:20] CORE (60 seconds)
        - 3-5 key points, each with:
        * Feature explanation (2-3 seconds)
        * Reality check / sarcastic undercut (1-2 seconds)
        * Code example or visual idea (2-3 seconds)

        [1:20-1:35] CONCLUSION (15 seconds)
        - Prediction with twist ending
        - Hot take or surprising angle
        - Sets up video hook

        [1:35-1:45] CTA (10 seconds)
        - "Like and subscribe" theme
        - Written in the topic's programming language or style

        B-ROLL SUGGESTIONS:
        - Code editor with syntax highlighting
        - Terminal output or compilation
        - Relevant diagrams or animations
        - Framework/tech logos"""

    def _get_code_report_template(self) -> str:
        """
        Template for longer code report format (3-5 minutes).

        Allows deeper technical dives with more context.
        """
        return """
        [0:00-0:10] HOOK (10 seconds)
        - Breaking news style delivery
        - Deadpan announcement
        - Teases the topic

        [0:10-0:30] CONTEXT (20 seconds)
        - Background: What led to this?
        - Why it matters now?
        - Industry timeline or comparison

        [0:30-2:30] DEEP DIVE (120 seconds)
        - Technical breakdown
        - 5-8 key points with examples
        - Reality checks and sarcastic interjections
        - Code snippets with actual production quality

        [2:30-3:00] HOT TAKES (30 seconds)
        - Community reactions
        - Your sarcastic take
        - Predictions for adoption/failure
        - Meme potential assessment

        [3:00-3:15] CTA (15 seconds)
        - Topic-relevant call to action
        - Written in topic's language

        B-ROLL SUGGESTIONS:
        - Code editor with real code
        - GitHub/GitLab screenshots
        - Architecture diagrams
        - Community comments or reactions
        - Relevant tech logos or frameworks
        - Terminal outputs"""

    def _get_tutorial_template(self) -> str:
        """
        Template for educational tutorial format.

        Balances education with entertainment.
        """
        return """
        [0:00-0:10] HOOK
        - What you'll learn
        - Why it's useful
        - Time commitment

        [0:10-0:30] PREREQUISITES
        - What you need to know
        - Tools required
        - Assumptions

        [0:30-X] MAIN CONTENT
        - Step-by-step progression
        - Each step: explain → show code → highlight key point
        - Keep pace brisk
        - Include "gotchas" and common mistakes

        [X-Y] TIPS & TRICKS
        - Advanced variations
        - Performance considerations
        - Best practices

        [Y-Z] SUMMARY & CTA
        - Key takeaways (3-5 points)
        - Encourage practice
        - Like, subscribe, etc.

        B-ROLL SUGGESTIONS:
        - Live coding walkthrough
        - Code editor with typing
        - Output/results visualization
        - Before/after comparisons
        - Code repository structure"""

    def estimate_reading_time(self, script: str) -> float:
        """
        Estimate reading/speaking time for a script in seconds.

        Based on average speaking pace of 150 words per minute (2.5 words/sec).

        Args:
            script: Script text to measure

        Returns:
            Estimated duration in seconds
        """
        word_count = len(script.split())
        # Average speaking pace: 150 words/minute = 2.5 words/second
        return word_count / 2.5
