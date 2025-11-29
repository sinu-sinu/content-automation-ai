from typing import Dict, List
from src.utils.openai_client import OpenAIClient
from pydantic import BaseModel
import json


class BrandScoreResponse(BaseModel):
    """Pydantic model for brand voice validation"""
    score: int  # 0-100
    reasoning: str
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]


class BrandVoiceAgent:
    """
    Flexible brand voice validator for any YouTube channel.

    Usage:
        # For Fireship
        fireship_validator = BrandVoiceAgent(client, fireship_profile, "Fireship")

        # For another channel
        veritasium_validator = BrandVoiceAgent(client, veritasium_profile, "Veritasium")
        astrum_validator = BrandVoiceAgent(client, astrum_profile, "Astrum")
    """

    def __init__(self, openai_client: OpenAIClient, brand_voice: Dict, channel_name: str):
        """
        Initialize brand voice validator.

        Args:
            openai_client: OpenAIClient instance
            brand_voice: Brand profile dictionary (loaded from JSON)
            channel_name: Name of the channel (used in system prompt for context)
        """
        self.client = openai_client
        self.brand_voice = brand_voice
        self.channel_name = channel_name

    def validate_script(self, script: str) -> Dict:
        """
        Score script against brand voice with GUARANTEED structure.

        Returns:
            Dict with: score, heuristic_score, llm_score, reasoning, strengths, weaknesses, suggestions
        """
        # Quick heuristic checks
        heuristic_score = self._heuristic_check(script)

        # LLM-based semantic check with structured output
        semantic_result = self._semantic_check_structured(script)

        # Combine scores: 40% heuristic + 60% LLM
        final_score = int(0.4 * heuristic_score + 0.6 * semantic_result.score)

        return {
            "score": final_score,
            "heuristic_score": heuristic_score,
            "llm_score": semantic_result.score,
            "reasoning": semantic_result.reasoning,
            "strengths": semantic_result.strengths,
            "weaknesses": semantic_result.weaknesses,
            "suggestions": semantic_result.suggestions
        }

    def _heuristic_check(self, script: str) -> int:
        """
        Fast pattern matching for brand voice characteristics.

        Checks:
        - Sentence length (should match pacing)
        - Signature phrases (bonus for each found)
        - Avoided terms (penalty for each found)
        """
        score = 70  # Base score

        # Check sentence length (should be short for fast-paced channels)
        sentences = [s.strip() for s in script.split('.') if s.strip()]
        if not sentences:
            return score

        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_length < 15:
            score += 10
        elif avg_length > 25:
            score -= 10

        # Check for signature phrases (bonus: +5 per phrase, max +15)
        found_phrases = sum(
            1 for phrase in self.brand_voice.get('signature_phrases', [])
            if phrase.lower() in script.lower()
        )
        score += min(found_phrases * 5, 15)

        # Check for avoided terms (penalty: -5 per term)
        found_bad = sum(
            1 for bad in self.brand_voice.get('avoid', [])
            if bad.lower() in script.lower()
        )
        score -= found_bad * 5

        return max(0, min(100, score))

    def _semantic_check_structured(self, script: str) -> BrandScoreResponse:
        """
        LLM-based brand voice matching with STRUCTURED OUTPUT.
        """
        # Build system prompt that's channel-agnostic
        system_prompt = f"""You are a brand voice expert analyzing YouTube scripts.

        Analyzing script for: {self.channel_name}

        Channel characteristics:
        {json.dumps(self.brand_voice, indent=2)}

        Analyze the script and provide:
        1. A score (0-100) for how well it matches {self.channel_name}'s style
        2. Clear reasoning for your score
        3. Specific strengths (what works well)
        4. Specific weaknesses (what doesn't match)
        5. Actionable suggestions for improvement

        Be precise and honest in your assessment."""

        user_message = f"""Analyze this script for {self.channel_name} brand voice consistency:

        {script}

        Provide detailed feedback."""

        # Use structured outputs - guaranteed parsing, no regex
        response = self.client.call_agent_structured(
            agent_type="validator",
            system_prompt=system_prompt,
            user_message=user_message,
            response_format=BrandScoreResponse
        )

        return response
