#!/usr/bin/env python3
"""
Integration tests for Phase 1 and Phase 2
Tests OpenAI client wrapper and Tech Scout Agent
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.openai_client import OpenAIClient
from src.utils.hn_scraper import get_trending_hn
from src.agents.tech_scout import TechScoutAgent


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.tests = []

    def add_pass(self, name, message=""):
        self.passed += 1
        self.tests.append(("PASS", name, message))
        print(f"[PASS] {name}")
        if message:
            print(f"   {message}")

    def add_fail(self, name, error):
        self.failed += 1
        self.tests.append(("FAIL", name, str(error)))
        print(f"[FAIL] {name}")
        print(f"   Error: {error}")

    def add_skip(self, name, reason=""):
        self.skipped += 1
        self.tests.append(("SKIP", name, reason))
        print(f"[SKIP] {name} (skipped)")
        if reason:
            print(f"   Reason: {reason}")

    def summary(self):
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        for status, name, message in self.tests:
            if status == "PASS":
                print(f"[PASS] {name}")
            elif status == "FAIL":
                print(f"[FAIL] {name}: {message[:60]}")
            else:
                print(f"[SKIP] {name}")

        total = self.passed + self.failed + self.skipped
        print(f"\nResults: {self.passed}/{total} passed, {self.failed} failed, {self.skipped} skipped")
        return self.failed == 0


results = TestResults()


# ============================================================================
# PHASE 1 TESTS: OpenAI Client Wrapper
# ============================================================================

def test_openai_client_initialization():
    """Test OpenAI client initializes correctly"""
    try:
        client = OpenAIClient()
        assert client.client is not None, "Client not initialized"
        assert "scout" in client.agent_models, "Scout model not configured"
        assert "writer" in client.agent_models, "Writer model not configured"
        assert "validator" in client.agent_models, "Validator model not configured"
        results.add_pass("OpenAI Client Initialization",
                        f"Models: {list(client.agent_models.keys())}")
    except Exception as e:
        results.add_fail("OpenAI Client Initialization", e)


def test_openai_client_has_api_key():
    """Test that API key is configured"""
    try:
        # Check both direct env var and OpenAI client initialization
        client = OpenAIClient()
        assert client.client is not None, "OpenAI client not initialized"
        # If we can create a client, API key is configured
        results.add_pass("OpenAI API Key", "API key configured and client initialized")
    except Exception as e:
        results.add_fail("OpenAI API Key", e)


def test_agent_temperature_config():
    """Test agent temperature configurations"""
    try:
        client = OpenAIClient()
        assert client.agent_temps["scout"] == 0.3, "Scout temp incorrect"
        assert client.agent_temps["writer"] == 0.8, "Writer temp incorrect"
        assert client.agent_temps["validator"] == 0.2, "Validator temp incorrect"
        results.add_pass("Agent Temperature Config",
                        f"Scout: {client.agent_temps['scout']}, Writer: {client.agent_temps['writer']}")
    except Exception as e:
        results.add_fail("Agent Temperature Config", e)


def test_call_agent_basic():
    """Test basic OpenAI API call"""
    try:
        client = OpenAIClient()
        response = client.call_agent(
            agent_type="scout",
            system_prompt="You are a helpful assistant.",
            user_message="Say 'Hello from Phase 1 test'",
            max_tokens=50
        )
        assert response, "No response from OpenAI"
        assert isinstance(response, str), "Response should be string"
        results.add_pass("OpenAI API Call",
                        f"Response: {response[:50]}...")
    except (ConnectionError, Exception) as e:
        if "Connection error" in str(e) or "401" in str(e) or "timeout" in str(e).lower():
            results.add_skip("OpenAI API Call", "No internet connection or API unavailable")
        else:
            results.add_fail("OpenAI API Call", e)


# ============================================================================
# PHASE 2 TESTS: Tech Scout Agent
# ============================================================================

def test_hn_scraper_function_exists():
    """Test HackerNews scraper function exists"""
    try:
        assert callable(get_trending_hn), "get_trending_hn not callable"
        results.add_pass("HN Scraper Function", "get_trending_hn() is callable")
    except Exception as e:
        results.add_fail("HN Scraper Function", e)


def test_cached_trends_file_exists():
    """Test cached trends JSON file exists and is valid"""
    try:
        # Get project root (parent of tests directory)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cache_file = os.path.join(project_root, "examples", "cached_hn_trending.json")
        assert os.path.exists(cache_file), f"Cache file not found: {cache_file}"

        with open(cache_file, 'r') as f:
            data = json.load(f)

        assert isinstance(data, list), "Cache should be a list"
        assert len(data) >= 10, f"Cache should have at least 10 items, got {len(data)}"

        # Validate structure
        required_fields = ["id", "title", "score", "url"]
        for item in data:
            for field in required_fields:
                assert field in item, f"Missing field '{field}' in cache item"

        results.add_pass("Cached Trends File",
                        f"Valid JSON with {len(data)} trending topics")
    except Exception as e:
        results.add_fail("Cached Trends File", e)


def test_brand_voice_config_exists():
    """Test Fireship brand voice config exists"""
    try:
        # Get project root (parent of tests directory)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_file = os.path.join(project_root, "config", "fireship_brand_voice.json")
        assert os.path.exists(config_file), f"Config file not found: {config_file}"

        with open(config_file, 'r') as f:
            config = json.load(f)

        required_fields = ["tone", "formality_level", "pacing", "signature_phrases", "avoid"]
        for field in required_fields:
            assert field in config, f"Missing required field: {field}"

        assert isinstance(config["tone"], list), "Tone should be a list"
        assert len(config["tone"]) > 0, "Tone list should not be empty"

        results.add_pass("Brand Voice Config",
                        f"Valid config with tone: {', '.join(config['tone'][:2])}")
    except Exception as e:
        results.add_fail("Brand Voice Config", e)


def test_tech_scout_agent_initialization():
    """Test Tech Scout Agent initializes correctly"""
    try:
        client = OpenAIClient()
        agent = TechScoutAgent(
            openai_client=client,
            channel_name="Fireship",
            demo_mode=True
        )

        assert agent.client is not None, "Client not set"
        assert agent.channel_name == "Fireship", "Channel name not set"
        assert agent.demo_mode == True, "Demo mode not set"
        assert agent.system_prompt is not None, "System prompt not created"
        assert len(agent.system_prompt) > 0, "System prompt is empty"

        results.add_pass("Tech Scout Initialization",
                        "Agent initialized with Fireship config")
    except Exception as e:
        results.add_fail("Tech Scout Initialization", e)


def test_tech_scout_brand_voice_loading():
    """Test Tech Scout loads brand voice correctly"""
    try:
        client = OpenAIClient()
        agent = TechScoutAgent(
            openai_client=client,
            channel_name="Fireship",
            demo_mode=True
        )

        assert agent.brand_voice is not None, "Brand voice not loaded"
        assert "tone" in agent.brand_voice, "Tone not in brand voice"
        assert "sarcastic" in agent.brand_voice["tone"], "Sarcastic tone missing"

        results.add_pass("Brand Voice Loading",
                        f"Loaded: {', '.join(agent.brand_voice['tone'][:2])}")
    except Exception as e:
        results.add_fail("Brand Voice Loading", e)


def test_tech_scout_system_prompt_includes_brand():
    """Test system prompt includes brand voice characteristics"""
    try:
        client = OpenAIClient()
        agent = TechScoutAgent(
            openai_client=client,
            channel_name="Fireship",
            demo_mode=True
        )

        prompt = agent.system_prompt.lower()
        assert "fireship" in prompt, "Fireship not mentioned in prompt"
        assert "sarcastic" in prompt or "humor" in prompt, "Humor style not in prompt"
        assert "developer" in prompt or "programmer" in prompt, "Developer focus not clear"

        results.add_pass("System Prompt Content",
                        "Prompt includes brand voice and Fireship context")
    except Exception as e:
        results.add_fail("System Prompt Content", e)


def test_tech_scout_get_trending_safe_demo_mode():
    """Test _get_trending_safe() in DEMO_MODE"""
    try:
        os.environ["DEMO_MODE"] = "true"
        client = OpenAIClient()
        agent = TechScoutAgent(
            openai_client=client,
            channel_name="Fireship",
            demo_mode=True
        )

        trending = agent._get_trending_safe()

        assert isinstance(trending, list), "Should return list"
        assert len(trending) > 0, "Should return trending items"
        assert "title" in trending[0], "Items should have title"
        assert "score" in trending[0], "Items should have score"

        results.add_pass("Get Trending (DEMO_MODE)",
                        f"Loaded {len(trending)} cached trending items")
    except Exception as e:
        results.add_fail("Get Trending (DEMO_MODE)", e)


def test_tech_scout_load_cached_trends():
    """Test _load_cached_trends() directly"""
    try:
        client = OpenAIClient()
        agent = TechScoutAgent(
            openai_client=client,
            channel_name="Fireship",
            demo_mode=True
        )

        trends = agent._load_cached_trends()

        assert isinstance(trends, list), "Should return list"
        assert len(trends) == 10, f"Should have 10 items, got {len(trends)}"
        assert all("title" in item for item in trends), "All items should have title"

        results.add_pass("Load Cached Trends",
                        f"Successfully loaded {len(trends)} trends")
    except Exception as e:
        results.add_fail("Load Cached Trends", e)


def test_tech_scout_select_best_topic():
    """Test _select_best_topic() with mock data"""
    try:
        client = OpenAIClient()
        agent = TechScoutAgent(
            openai_client=client,
            channel_name="Fireship",
            demo_mode=True
        )

        mock_trends = [
            {"title": "React 19 Released", "score": 856},
            {"title": "Python Async/Await", "score": 742},
            {"title": "TypeScript 5.5", "score": 531}
        ]

        selected = agent._select_best_topic(mock_trends)

        assert isinstance(selected, str), "Should return string"
        assert len(selected) > 0, "Should return non-empty topic"
        # Topic should be one of the inputs
        assert any(topic["title"] in selected for topic in mock_trends) or \
               "javascript" in selected.lower() or \
               "framework" in selected.lower(), "Should select a real or plausible topic"

        results.add_pass("Select Best Topic",
                        f"Selected: {selected[:50]}")
    except Exception as e:
        if "Connection error" in str(e):
            results.add_skip("Select Best Topic", "API unavailable for topic selection")
        else:
            results.add_fail("Select Best Topic", e)


def test_tech_scout_research_topic_with_specific_topic():
    """Test research_topic() with a specific topic"""
    try:
        client = OpenAIClient()
        agent = TechScoutAgent(
            openai_client=client,
            channel_name="Fireship",
            demo_mode=True
        )

        result = agent.research_topic(topic="Python async/await patterns")

        assert isinstance(result, dict), "Should return dict"
        assert "topic" in result, "Should have topic"
        assert "brief" in result, "Should have brief"
        assert "sources" in result, "Should have sources"
        assert "mode" in result, "Should have mode"

        assert result["topic"] == "Python async/await patterns", "Topic should match input"
        assert len(result["brief"]) > 100, "Brief should have substantial content"
        assert isinstance(result["brief"], str), "Brief should be string"

        results.add_pass("Research Topic (Specific)",
                        f"Researched '{result['topic']}'")
    except Exception as e:
        if "Connection error" in str(e):
            results.add_skip("Research Topic (Specific)", "API unavailable for research")
        else:
            results.add_fail("Research Topic (Specific)", e)


def test_tech_scout_research_topic_auto_discover():
    """Test research_topic() with auto-discovery"""
    try:
        os.environ["DEMO_MODE"] = "true"
        client = OpenAIClient()
        agent = TechScoutAgent(
            openai_client=client,
            channel_name="Fireship",
            demo_mode=True
        )

        result = agent.research_topic()  # No topic provided

        assert isinstance(result, dict), "Should return dict"
        assert "topic" in result, "Should have topic"
        assert "brief" in result, "Should have brief"
        assert len(result["topic"]) > 0, "Topic should be selected"
        assert len(result["brief"]) > 0, "Brief should be generated"
        assert result["mode"] == "cached", "Should use cached mode in DEMO_MODE"

        results.add_pass("Research Topic (Auto-Discover)",
                        f"Auto-selected and researched: {result['topic'][:40]}...")
    except Exception as e:
        if "Connection error" in str(e):
            results.add_skip("Research Topic (Auto-Discover)", "API unavailable for topic discovery")
        else:
            results.add_fail("Research Topic (Auto-Discover)", e)


# ============================================================================
# CONSISTENCY CHECKS
# ============================================================================

def test_consistency_phase1_phase2():
    """Verify Phase 1 and Phase 2 are properly integrated"""
    try:
        client = OpenAIClient()
        agent = TechScoutAgent(
            openai_client=client,
            channel_name="Fireship",
            demo_mode=True
        )

        # Phase 1 - OpenAI client should work
        assert client.client is not None

        # Phase 2 - Agent should use Phase 1 client
        assert agent.client == client

        # Integration test
        result = agent.research_topic(topic="Test topic")
        assert result["brief"] is not None

        results.add_pass("Phase 1 & Phase 2 Integration",
                        "Agent properly uses OpenAI client wrapper")
    except Exception as e:
        if "Connection error" in str(e):
            results.add_skip("Phase 1 & Phase 2 Integration", "API unavailable for integration test")
        else:
            results.add_fail("Phase 1 & Phase 2 Integration", e)


def test_consistency_demo_mode_flag():
    """Test DEMO_MODE environment variable is respected"""
    try:
        # Test with DEMO_MODE=true
        os.environ["DEMO_MODE"] = "true"
        client = OpenAIClient()
        agent1 = TechScoutAgent(openai_client=client, demo_mode=False)
        assert agent1.demo_mode == True, "Should respect DEMO_MODE env var"

        # Test with DEMO_MODE=false
        os.environ["DEMO_MODE"] = "false"
        agent2 = TechScoutAgent(openai_client=client, demo_mode=False)
        assert agent2.demo_mode == False, "Should respect DEMO_MODE=false"

        results.add_pass("DEMO_MODE Environment Variable",
                        "Respects both env var and parameter")
    except Exception as e:
        results.add_fail("DEMO_MODE Environment Variable", e)


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests"""
    print("\n" + "[TEST]" * 20)
    print("PHASE 1 & PHASE 2 TEST SUITE")
    print("[TEST]" * 20 + "\n")

    print("=" * 70)
    print("PHASE 1: OpenAI Client Wrapper")
    print("=" * 70)
    test_openai_client_initialization()
    test_openai_client_has_api_key()
    test_agent_temperature_config()
    test_call_agent_basic()

    print("\n" + "=" * 70)
    print("PHASE 2: Tech Scout Agent")
    print("=" * 70)
    test_hn_scraper_function_exists()
    test_cached_trends_file_exists()
    test_brand_voice_config_exists()
    test_tech_scout_agent_initialization()
    test_tech_scout_brand_voice_loading()
    test_tech_scout_system_prompt_includes_brand()
    test_tech_scout_get_trending_safe_demo_mode()
    test_tech_scout_load_cached_trends()
    test_tech_scout_select_best_topic()
    test_tech_scout_research_topic_with_specific_topic()
    test_tech_scout_research_topic_auto_discover()

    print("\n" + "=" * 70)
    print("INTEGRATION & CONSISTENCY")
    print("=" * 70)
    test_consistency_phase1_phase2()
    test_consistency_demo_mode_flag()

    return results.summary()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
