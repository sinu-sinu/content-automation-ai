#!/usr/bin/env python3
"""
Main entry point: Run complete workflow for any channel

Flow:
  User Input: channel name + topic
    |
    v
  [Phase 2] Tech Scout Agent -> Research topic
    |
    v
  [Phase 3] Script Writer Agent -> Generate script from research
    |
    v
  [Phase 4] Brand Voice Validator -> Validate script matches channel
    |
    v
  Output: Final script + brand score

Usage: python run.py
"""

import sys
from dotenv import load_dotenv
from src.utils.openai_client import OpenAIClient
from src.utils.brand_voice_loader import load_brand_voice
from src.agents.brand_voice import BrandVoiceAgent

# Load environment variables from .env
load_dotenv()


def run_workflow(channel_name: str, topic: str, format_type: str = "100_seconds"):
    """
    Complete workflow: Research -> Write -> Validate

    Args:
        channel_name: Channel to generate content for
        topic: Topic to research and write about
        format_type: Video format (100_seconds, code_report, tutorial)

    Returns:
        dict with final_script, brand_score, validation_details
    """

    print("\n" + "=" * 70)
    print("WORKFLOW EXECUTION")
    print("=" * 70)
    print(f"Channel: {channel_name}")
    print(f"Topic: {topic}")
    print(f"Format: {format_type}")
    print("=" * 70)

    try:
        # Initialize OpenAI client
        client = OpenAIClient()
        print("\n[INIT] OpenAI client ready")

        # Load brand voice profile
        brand_profile = load_brand_voice(channel_name)
        print(f"[INIT] Loaded brand profile: {brand_profile.get('channel_name')}")

        # Phase 2: Tech Scout Agent
        print("\n[PHASE 2] Tech Scout Agent - Researching topic...")
        print("  STATUS: TODO - Phase 2 not yet implemented")
        print("  EXPECTED: research_brief dict with topic analysis")
        research_brief = {
            "topic": topic,
            "brief": "[TODO: Research brief from Tech Scout Agent]",
            "sources": []
        }
        print(f"  OUTPUT: Placeholder research brief")

        # Phase 3: Script Writer Agent
        print("\n[PHASE 3] Script Writer Agent - Generating script...")
        print("  STATUS: TODO - Phase 3 not yet implemented")
        print("  EXPECTED: draft_script string in Fireship style")
        draft_script = "[TODO: Generated script from Script Writer Agent]"
        print(f"  OUTPUT: Placeholder script")

        # Phase 4: Brand Voice Validator
        print("\n[PHASE 4] Brand Voice Validator - Validating script...")
        validator = BrandVoiceAgent(client, brand_profile, channel_name)
        validation_result = validator.validate_script(draft_script)
        print(f"  OUTPUT: Brand score {validation_result['score']}/100")

        # Results
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Channel: {channel_name}")
        print(f"Topic: {topic}")
        print(f"Brand Score: {validation_result['score']}/100")
        print(f"  - Heuristic: {validation_result['heuristic_score']}/100")
        print(f"  - LLM Score: {validation_result['llm_score']}/100")

        if validation_result['score'] >= 75:
            print(f"\nStatus: PASSED (score >= 75)")
        else:
            print(f"\nStatus: NEEDS REFINEMENT (score < 75)")
            print("\nSuggestions for improvement:")
            for i, suggestion in enumerate(validation_result['suggestions'], 1):
                print(f"  {i}. {suggestion}")

        print("\n" + "=" * 70)
        print("SUCCESS: Workflow completed")
        print("=" * 70 + "\n")

        return {
            "channel": channel_name,
            "topic": topic,
            "format": format_type,
            "research_brief": research_brief,
            "draft_script": draft_script,
            "brand_score": validation_result['score'],
            "validation": validation_result
        }

    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("\nAvailable channels in config/:")
        print("  - fireship")
        print("\nTo add a new channel:")
        print("  1. Create config/{channel}_brand_voice.json")
        print("  2. Use load_brand_voice('{channel}')")
        print("  3. Run: python run.py\n")
        sys.exit(1)

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Check if .env file exists with OPENAI_API_KEY")
        print("  2. Check if channel config file exists in config/")
        print("  3. Check OpenAI API key is valid\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Interactive entry point"""

    print("\n" + "=" * 70)
    print("automate channel content - Multi-Channel Workflow Runner")
    print("=" * 70)

    # Get channel name
    channel = input("\nEnter channel name (e.g., fireship): ").strip().lower()
    if not channel:
        print("ERROR: Channel name cannot be empty")
        return

    # Get topic
    topic = input("Enter topic to research and write about: ").strip()
    if not topic:
        print("ERROR: Topic cannot be empty")
        return

    # Get format (optional)
    format_type = input("Enter format (100_seconds/code_report/tutorial) [default: 100_seconds]: ").strip().lower()
    if format_type not in ["100_seconds", "code_report", "tutorial"]:
        format_type = "100_seconds"

    # Run workflow
    result = run_workflow(channel, topic, format_type)

    return result


if __name__ == "__main__":
    main()
