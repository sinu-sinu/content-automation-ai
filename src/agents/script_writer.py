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
        
        FORMATTING REQUIREMENTS (CRITICAL):
        - Put TWO blank lines after each timestamp header (e.g., [0:00-0:15] HOOK)
        - Use markdown formatting for code blocks: ```language
        - Use **bold** for emphasis
        - Use proper paragraph breaks between ideas
        - Each section should be clearly separated with blank lines
        - Example format:
        
        [0:00-0:15] HOOK
        
        
        Your hook text here. Keep it punchy.
        
        
        [0:15-0:45] CONTEXT
        
        
        Your context text here.

        Write the COMPLETE script now with proper formatting:"""

        script = self.client.call_agent(
            agent_type="writer",
            system_prompt=self.system_prompt,
            user_message=user_message,
            model="gpt-4o",  # Use best model for creative writing
            temperature=0.8,
            max_tokens=8000  # Increased for longer code_report format (4-5 min)
        )

        # Post-process for clean formatting
        script = self._clean_script_formatting(script)

        return script

    def _clean_script_formatting(self, script: str) -> str:
        """
        Post-process script to ensure clean formatting and proper markdown.
        
        Fixes common formatting issues:
        - Ensures blank lines after timestamp headers
        - Fixes markdown code blocks
        - Adds proper spacing between sections
        
        Args:
            script: Raw script from LLM
            
        Returns:
            Cleaned and formatted script
        """
        import re
        
        # Split into lines for processing
        lines = script.split('\n')
        cleaned_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a timestamp header (e.g., [0:00-0:15] HOOK)
            if re.match(r'^\[[\d:]+\-[\d:]+\]', line.strip()):
                # Add the timestamp header
                cleaned_lines.append(line)
                # Ensure we have blank lines after it
                cleaned_lines.append('')
                cleaned_lines.append('')
                
                # Skip any immediate blank lines in original
                i += 1
                while i < len(lines) and lines[i].strip() == '':
                    i += 1
                continue
            
            # Regular line - just add it
            cleaned_lines.append(line)
            i += 1
        
        # Join back together
        cleaned_script = '\n'.join(cleaned_lines)
        
        # Fix code block formatting - ensure proper markdown
        # Replace any malformed code blocks
        cleaned_script = re.sub(
            r'```(\w+)?\s*\n',
            r'```\1\n',
            cleaned_script
        )
        
        # Ensure sections are separated by at least one blank line
        cleaned_script = re.sub(r'\n{4,}', '\n\n\n', cleaned_script)  # Max 3 newlines
        
        # Clean up any trailing whitespace
        lines = [line.rstrip() for line in cleaned_script.split('\n')]
        cleaned_script = '\n'.join(lines)
        
        return cleaned_script

    def _get_100s_template(self) -> str:
        """
        Template for 100-second YouTube shorts format.

        Paces to exactly 100 seconds with clear section breaks.
        """
        return """[0:00-0:05] HOOK
        
        State something obvious in deadpan way. Grab attention immediately.
        Single punchy sentence.
        
        
        [0:05-0:20] SETUP
        
        What is this thing? Why should you care? Add light sarcasm here.
        2-3 sentences with quick context.
        
        
        [0:20-1:20] CORE
        
        Present 3-5 key points. For each point:
        - Feature explanation (2-3 seconds)
        - Reality check / sarcastic undercut (1-2 seconds)  
        - Code example or visual idea (2-3 seconds)
        
        Use proper markdown for any code blocks.
        
        
        [1:20-1:35] CONCLUSION
        
        Prediction with twist ending. Hot take or surprising angle.
        Sets up the video hook with your signature delivery.
        
        
        [1:35-1:45] CTA
        
        "Like and subscribe" theme. Written in the topic's programming language or style.
        Make it clever.
        
        
        ---
        
        **B-ROLL SUGGESTIONS:**
        - Code editor with syntax highlighting
        - Terminal output or compilation
        - Relevant diagrams or animations
        - Framework/tech logos"""

    def _get_code_report_template(self) -> str:
        """
        Template for longer code report format (4-5 minutes).

        Allows deeper technical dives with more context and examples.
        """
        return """[0:00-0:15] HOOK
        
        Breaking news style delivery. Deadpan announcement. Tease the topic with a bold statement.
        Write 2-3 punchy sentences that grab attention immediately.
        
        
        [0:15-0:45] CONTEXT
        
        Provide background: What led to this? Why it matters now?
        Include industry timeline or comparison. Who's behind it? What problem does it solve?
        Write 3-4 sentences with clear context.
        
        
        [0:45-1:15] THE BASICS
        
        Core concept explanation. Main architecture or approach.
        Quick comparison to alternatives. "Here's how it actually works" moment.
        Include a simple code example if relevant.
        
        
        [1:15-3:15] DEEP DIVE
        
        Technical breakdown in 6-10 key points. Include:
        - Code examples with real-world scenarios (use proper markdown code blocks)
        - Reality checks and sarcastic interjections
        - Performance considerations
        - Trade-offs and gotchas
        - Production quality code snippets
        - Edge cases or common mistakes
        
        Each point should be 10-20 seconds. Use clear paragraph breaks.
        
        
        [3:15-3:45] PRACTICAL USE CASES
        
        When to use it (and when NOT to). Real-world applications.
        Who's already using this in production? Performance implications?
        Be specific with examples.
        
        
        [3:45-4:15] HOT TAKES & PREDICTIONS
        
        Community reactions and drama. Your sarcastic take on adoption.
        Predictions for success/failure. Twitter/Reddit sentiment.
        Meme potential assessment.
        
        
        [4:15-4:30] WRAP UP
        
        Final verdict with twist. One-liner summary. Callback to hook.
        End with your signature deadpan delivery.
        
        
        [4:30-4:45] CTA
        
        Topic-relevant call to action. Written in topic's language or style.
        Make it clever and on-brand.
        
        
        ---
        
        **B-ROLL SUGGESTIONS:**
        - Code editor with real code examples
        - GitHub/GitLab screenshots
        - Architecture diagrams
        - Community comments or reactions
        - Relevant tech logos or frameworks
        - Terminal outputs and builds
        - Performance benchmarks or metrics
        - Side-by-side comparisons"""

    def _get_tutorial_template(self) -> str:
        """
        Template for educational tutorial format.

        Balances education with entertainment.
        """
        return """[0:00-0:10] HOOK
        
        What you'll learn. Why it's useful. Time commitment.
        Make it compelling and clear about the outcome.
        
        
        [0:10-0:30] PREREQUISITES
        
        What you need to know. Tools required. Assumptions about skill level.
        Be specific so viewers can follow along.
        
        
        [0:30-X] MAIN CONTENT
        
        Step-by-step progression. For each step:
        1. Explain the concept (what and why)
        2. Show the code (use proper markdown code blocks)
        3. Highlight the key point or gotcha
        
        Keep pace brisk. Include common mistakes and how to avoid them.
        Use clear paragraph breaks between steps.
        
        
        [X-Y] TIPS & TRICKS
        
        Advanced variations. Performance considerations. Best practices.
        Share pro tips that separate beginners from experts.
        
        
        [Y-Z] SUMMARY & CTA
        
        Key takeaways (3-5 points). Encourage practice and experimentation.
        Like, subscribe, etc. with a topic-relevant twist.
        
        
        ---
        
        **B-ROLL SUGGESTIONS:**
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
