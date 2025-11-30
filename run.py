#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point: Run complete LangGraph workflow

Now uses Phase 5 orchestration with self-correcting workflow loop.

Flow:
  Scout → Draft → Validate → [Refine if score < 75] → END

Usage:
  python run.py                          # Interactive mode
  python run.py --topic "React 19"       # Direct topic
  python run.py --auto                   # Auto-discover trending topic
  python run.py --demo                   # Demo mode (cached data)
"""

import sys
import argparse
import io
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from src.orchestrator.workflow import run_workflow
from src.utils.openai_client import OpenAIClient

# Load environment variables from .env
load_dotenv()


def main():
    """Entry point with CLI arguments or interactive mode"""
    
    parser = argparse.ArgumentParser(
        description="Electrify: AI-powered YouTube script generator with LangGraph orchestration"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Topic to research and write about (or leave empty for auto-discovery)"
    )
    parser.add_argument(
        "--format",
        type=str,
        default="code_report",
        choices=["100_seconds", "code_report", "tutorial"],
        help="Script format type (default: code_report - typical 4-5 min video)"
    )
    parser.add_argument(
        "--channel",
        type=str,
        default="Fireship",
        help="Channel name for brand voice (default: Fireship)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo mode (cached data for reliability)"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-discover trending topic from HackerNews"
    )
    
    args = parser.parse_args()
    
    # Interactive mode if no arguments
    if len(sys.argv) == 1:
        return interactive_mode()
    
    # CLI mode
    return cli_mode(args)


def interactive_mode():
    """Interactive prompts for user input"""
    
    print("\n" + "=" * 70)
    print("ELECTRIFY - AI YouTube Script Generator")
    print("Powered by LangGraph Orchestration (Phase 5)")
    print("=" * 70)
    
    # Get channel name
    print("\n Channel Configuration")
    channel = input("Enter channel name [default: Fireship]: ").strip()
    if not channel:
        channel = "Fireship"
    
    # Get topic (or auto-discover)
    print("\n Topic Selection")
    print("Options:")
    print("  1. Provide a specific topic")
    print("  2. Auto-discover trending topic from HackerNews")
    
    choice = input("Choose (1 or 2) [default: 2]: ").strip()
    
    if choice == "1":
        topic = input("Enter topic: ").strip()
        if not topic:
            print("ERROR: Topic cannot be empty")
            return
    else:
        topic = None  # Will auto-discover
        print(" Will auto-discover trending topic")
    
    # Get format
    print("\n Script Format")
    print("Options:")
    print("  1. code_report - Typical Fireship video (4-5 min) [DEFAULT]")
    print("  2. 100_seconds - Quick explainer format (~2 min)")
    print("  3. tutorial - Educational deep-dive")
    format_type = input("Enter format [default: code_report]: ").strip().lower()
    if format_type not in ["100_seconds", "code_report", "tutorial"]:
        format_type = "code_report"
    
    # Demo mode
    print("\nExecution Mode")
    demo_input = input("Use demo mode (cached data)? (y/n) [default: n]: ").strip().lower()
    demo_mode = demo_input in ["y", "yes", "true", "1"]
    
    print("\n" + "=" * 70)
    print("Starting workflow...")
    print("=" * 70)
    
    # Run workflow
    try:
        client = OpenAIClient()
        result = run_workflow(
            topic=topic,
            format_type=format_type,
            channel_name=channel,
            demo_mode=demo_mode,
            openai_client=client
        )
        
        print_results(result)
        return result
        
    except FileNotFoundError as e:
        print(f"\n ERROR: {e}")
        print("\n Available channels in config/:")
        print("  - Fireship (config/fireship_brand_voice.json)")
        print("\nTo add a new channel:")
        print("  1. Create config/{channel_name}_brand_voice.json")
        print("  2. Use the same structure as fireship_brand_voice.json")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        print("\n Troubleshooting:")
        print("  1. Check if .env file exists with OPENAI_API_KEY")
        print("  2. Check if channel config file exists in config/")
        print("  3. Verify OpenAI API key is valid")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cli_mode(args):
    """Run workflow with CLI arguments"""
    
    print("\n" + "=" * 70)
    print("ELECTRIFY - AI YouTube Script Generator")
    print("=" * 70)
    print(f"Channel: {args.channel}")
    print(f"Topic: {args.topic or 'Auto-discover'}")
    print(f"Format: {args.format}")
    print(f"Demo Mode: {args.demo}")
    print("=" * 70 + "\n")
    
    try:
        client = OpenAIClient()
        result = run_workflow(
            topic=args.topic if not args.auto else None,
            format_type=args.format,
            channel_name=args.channel,
            demo_mode=args.demo,
            openai_client=client
        )
        
        print_results(result)
        return result
        
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_results(result):
    """Print formatted workflow results"""
    
    print("\n" + "=" * 70)
    print("WORKFLOW RESULTS")
    print("=" * 70)
    
    print(f"\n Execution Summary")
    print(f"  Topic: {result.get('topic', 'N/A')}")
    print(f"  Format: {result.get('format_type', 'N/A')}")
    print(f"  Execution Mode: {result.get('execution_mode', 'N/A')}")
    print(f"  Refinement Iterations: {result.get('iteration', 0)}")
    
    print(f"\n Validation Scores")
    print(f"  Final Score: {result.get('brand_score', 0)}/100")
    print(f"  Heuristic Score: {result.get('heuristic_score', 0)}/100")
    print(f"  LLM Score: {result.get('llm_score', 0)}/100")
    
    if result.get('brand_score', 0) >= 75:
        print(f"  Status: PASSED (score >= 75)")
    else:
        print(f"  Status: NEEDS IMPROVEMENT (score < 75)")
    
    # Show validation feedback
    if result.get('validation_strengths'):
        print(f"\n Strengths:")
        for strength in result['validation_strengths']:
            print(f"  • {strength}")
    
    if result.get('validation_weaknesses'):
        print(f"\n  Weaknesses:")
        for weakness in result['validation_weaknesses']:
            print(f"  • {weakness}")
    
    if result.get('validation_suggestions'):
        print(f"\n Suggestions:")
        for suggestion in result['validation_suggestions']:
            print(f"  • {suggestion}")
    
    # Show final script
    if result.get('final_script'):
        print(f"\n Final Script")
        print("=" * 70)
        print(result['final_script'])
        print("=" * 70)
    
    # Show errors if any
    if result.get('errors'):
        print(f"\n Errors:")
        for error in result['errors']:
            print(f"  • {error}")
    
    print("\n" + "=" * 70)
    print(" Workflow Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
