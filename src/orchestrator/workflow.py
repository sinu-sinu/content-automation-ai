"""
LangGraph Orchestration Workflow

Coordinates three agents into a self-correcting workflow:
1. Scout: Research trending topics
2. Writer: Generate scripts
3. Validator: Score brand voice compliance

Flow:
  Scout → Draft → Validate → [Refine if score < 75] → END
"""

from typing import TypedDict, Optional, List, Literal
from langgraph.graph import StateGraph, END
from src.agents.tech_scout import TechScoutAgent
from src.agents.script_writer import ScriptWriterAgent
from src.agents.brand_voice import BrandVoiceAgent
from src.utils.openai_client import OpenAIClient
from src.utils.brand_voice_loader import load_brand_voice
import os


class WorkflowState(TypedDict):
    """
    State management for the complete workflow.

    Fields flow through agents and get updated at each step.
    """
    # Input
    topic: Optional[str]
    format_type: str

    # Scout output
    research_brief: Optional[str]
    research_sources: Optional[List[str]]

    # Writer output
    draft_script: Optional[str]

    # Validator output
    brand_score: Optional[int]
    heuristic_score: Optional[int]
    llm_score: Optional[int]
    validation_reasoning: Optional[str]
    validation_strengths: Optional[List[str]]
    validation_weaknesses: Optional[List[str]]
    validation_suggestions: Optional[List[str]]

    # Refinement tracking
    final_script: Optional[str]
    iteration: int
    should_refine: bool

    # Error handling
    errors: List[str]
    execution_mode: str  # "live" or "cached"


def scout_node(state: WorkflowState, scout: TechScoutAgent) -> WorkflowState:
    """
    Node 1: Research topic using TechScoutAgent.

    Takes optional topic from input, auto-discovers if not provided.
    Updates state with research brief and sources.
    """
    try:
        print(f"\n[SCOUT] Researching topic: {state.get('topic', 'auto-discover')}")

        result = scout.research_topic(state.get('topic'))

        state['research_brief'] = result['brief']
        state['research_sources'] = result.get('sources', [])
        state['execution_mode'] = result.get('mode', 'live')
        state['topic'] = result['topic']

        print(f"[SCOUT] Research complete. Topic: {state['topic']}")
        return state

    except Exception as e:
        error_msg = f"Scout error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        state['errors'].append(error_msg)
        raise


def draft_node(state: WorkflowState, writer: ScriptWriterAgent) -> WorkflowState:
    """
    Node 2: Generate script using ScriptWriterAgent.

    Takes research brief from scout output.
    Updates state with draft script.
    """
    try:
        print(f"\n[WRITER] Generating {state['format_type']} script...")

        if not state.get('research_brief'):
            raise ValueError("No research brief available for script generation")

        script = writer.generate_script(
            research_brief=state['research_brief'],
            format_type=state['format_type']
        )

        state['draft_script'] = script
        print(f"[WRITER] Script generated ({len(script)} chars)")
        return state

    except Exception as e:
        error_msg = f"Writer error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        state['errors'].append(error_msg)
        raise


def validate_node(state: WorkflowState, validator: BrandVoiceAgent) -> WorkflowState:
    """
    Node 3: Validate script against brand voice using BrandVoiceAgent.

    Takes draft script from writer output.
    Updates state with validation scores and feedback.
    """
    try:
        print(f"\n[VALIDATOR] Scoring script against brand voice...")

        if not state.get('draft_script'):
            raise ValueError("No draft script available for validation")

        result = validator.validate_script(state['draft_script'])

        state['brand_score'] = result['score']
        state['heuristic_score'] = result['heuristic_score']
        state['llm_score'] = result['llm_score']
        state['validation_reasoning'] = result['reasoning']
        state['validation_strengths'] = result['strengths']
        state['validation_weaknesses'] = result['weaknesses']
        state['validation_suggestions'] = result['suggestions']

        print(f"[VALIDATOR] Score: {state['brand_score']}/100 (Heuristic: {state['heuristic_score']}, LLM: {state['llm_score']})")

        # Determine if refinement is needed
        if state['brand_score'] < 75 and state['iteration'] < 2:
            state['should_refine'] = True
            print(f"[VALIDATOR] Score < 75, will refine (iteration {state['iteration']} of 2)")
        else:
            state['should_refine'] = False
            if state['brand_score'] >= 75:
                print(f"[VALIDATOR] Score >= 75, script accepted!")
            else:
                print(f"[VALIDATOR] Max refinements reached, using current script")

        return state

    except Exception as e:
        error_msg = f"Validator error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        state['errors'].append(error_msg)
        raise


def refine_node(state: WorkflowState, writer: ScriptWriterAgent) -> WorkflowState:
    """
    Node 4: Refine script based on validator feedback.

    Takes validation suggestions and regenerates script.
    Updates iteration counter and draft script.
    """
    try:
        state['iteration'] += 1
        print(f"\n[REFINE] Refining script (iteration {state['iteration']}/2)...")

        if not state.get('draft_script'):
            raise ValueError("No draft script to refine")

        # Build refinement prompt with validator feedback
        refinement_prompt = f"""Previous script feedback:

        Weaknesses:
        {chr(10).join(f"- {w}" for w in state['validation_weaknesses'])}

        Suggestions for improvement:
        {chr(10).join(f"- {s}" for s in state['validation_suggestions'])}

        Original script to refine:
        {state['draft_script']}

        Please refine the script addressing the weaknesses and suggestions above."""

        refined_script = writer.generate_script(
            research_brief=refinement_prompt,
            format_type=state['format_type']
        )

        state['draft_script'] = refined_script
        print(f"[REFINE] Script refined ({len(refined_script)} chars)")
        return state

    except Exception as e:
        error_msg = f"Refine error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        state['errors'].append(error_msg)
        raise


def should_refine(state: WorkflowState) -> str:
    """
    Conditional edge logic: Decide whether to refine or end.

    Returns:
        "refine" if score < 75 and iteration < 2
        END otherwise
    """
    if state.get('should_refine', False) and state['iteration'] < 2:
        return "refine"
    return END


def build_workflow(openai_client: OpenAIClient, channel_name: str = "Fireship", demo_mode: bool = False):
    """
    Build and compile the LangGraph workflow.

    Args:
        openai_client: OpenAI client for all agents
        channel_name: YouTube channel name
        demo_mode: Whether to use demo mode for reliability

    Returns:
        Compiled graph ready for execution
    """
    # Initialize agents
    scout = TechScoutAgent(openai_client, channel_name=channel_name, demo_mode=demo_mode)
    writer = ScriptWriterAgent(openai_client, channel_name=channel_name, demo_mode=demo_mode)
    brand_voice = load_brand_voice(channel_name)
    validator = BrandVoiceAgent(openai_client, brand_voice, channel_name)

    # Create graph
    workflow = StateGraph(WorkflowState)

    # Add nodes - wrap with lambda to pass agents
    workflow.add_node("scout", lambda state: scout_node(state, scout))
    workflow.add_node("draft", lambda state: draft_node(state, writer))
    workflow.add_node("validate", lambda state: validate_node(state, validator))
    workflow.add_node("refine", lambda state: refine_node(state, writer))

    # Add edges
    workflow.add_edge("scout", "draft")  # Scout always leads to draft
    workflow.add_edge("draft", "validate")  # Draft always leads to validate

    # Conditional edge from validate
    workflow.add_conditional_edges(
        "validate",
        should_refine,
        {
            "refine": "refine",
            END: END
        }
    )

    # Edge from refine back to validate (loop)
    workflow.add_edge("refine", "validate")

    # Set entry point
    workflow.set_entry_point("scout")

    # Compile
    app = workflow.compile()

    return app


def run_workflow(
    topic: Optional[str] = None,
    format_type: str = "100_seconds",
    channel_name: str = "Fireship",
    demo_mode: bool = False,
    openai_client: Optional[OpenAIClient] = None
) -> WorkflowState:
    """
    Execute the complete workflow.

    Main entry point for the orchestration system.

    Args:
        topic: Topic to research (optional, auto-discovers if None)
        format_type: Script format ("100_seconds", "code_report", "tutorial")
        channel_name: YouTube channel name
        demo_mode: Use demo mode for reliability (DEMO_MODE env var overrides)
        openai_client: OpenAI client (creates one if None)

    Returns:
        Final workflow state with generated script and metadata

    Example:
        result = run_workflow(
            topic="WebAssembly",
            format_type="100_seconds",
            channel_name="Fireship",
            demo_mode=True
        )
        print(f"Final Script:\\n{result['final_script']}")
        print(f"Score: {result['brand_score']}/100")
    """
    # Create client if not provided
    if openai_client is None:
        openai_client = OpenAIClient()

    # Check environment for demo mode override
    demo_mode = demo_mode or os.getenv("DEMO_MODE", "false").lower() == "true"

    print("\n" + "="*80)
    print("FIRESHIP AI WORKFLOW")
    print("="*80)
    print(f"Topic: {topic or 'auto-discover'}")
    print(f"Format: {format_type}")
    print(f"Channel: {channel_name}")
    print(f"Mode: {'DEMO' if demo_mode else 'LIVE'}")
    print("="*80)

    try:
        # Build workflow
        app = build_workflow(openai_client, channel_name, demo_mode)

        # Initialize state
        initial_state: WorkflowState = {
            "topic": topic,
            "format_type": format_type,
            "research_brief": None,
            "research_sources": None,
            "draft_script": None,
            "brand_score": None,
            "heuristic_score": None,
            "llm_score": None,
            "validation_reasoning": None,
            "validation_strengths": None,
            "validation_weaknesses": None,
            "validation_suggestions": None,
            "final_script": None,
            "iteration": 0,
            "should_refine": False,
            "errors": [],
            "execution_mode": "live"
        }

        # Run workflow
        print("\nStarting workflow execution...\n")
        final_state = app.invoke(initial_state)

        # Set final script
        final_state['final_script'] = final_state.get('draft_script', None)

        # Print summary
        print("\n" + "="*80)
        print("WORKFLOW COMPLETE")
        print("="*80)
        print(f"Topic: {final_state['topic']}")
        print(f"Iterations: {final_state['iteration']}")
        print(f"Brand Score: {final_state['brand_score']}/100")
        print(f"Execution Mode: {final_state['execution_mode']}")

        if final_state['errors']:
            print(f"Errors: {len(final_state['errors'])}")
            for error in final_state['errors']:
                print(f"  - {error}")
        else:
            print("Status: Success")

        print("="*80 + "\n")

        return final_state

    except Exception as e:
        print(f"\n[FATAL] Workflow execution failed: {e}")
        import traceback
        traceback.print_exc()

        # Return state with error
        initial_state['errors'].append(f"Workflow fatal error: {str(e)}")
        initial_state['final_script'] = None
        return initial_state
