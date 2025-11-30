"""
Streamlit Demo UI for Content Automation

Multi-Agent LangGraph Orchestration Interface
"""

import streamlit as st
import sys
import os
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.orchestrator.workflow import run_workflow
from src.utils.openai_client import OpenAIClient


# =============================================================================
# PAGE CONFIGURATION 
# =============================================================================

st.set_page_config(
    page_title="Content Video Prototype",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# SESSION STATE INITIALIZATION 
# =============================================================================

def initialize_session_state():
    """Initialize session state variables for better UX"""
    if 'api_key' not in st.session_state:
        st.session_state['api_key'] = ''
    if 'last_result' not in st.session_state:
        st.session_state['last_result'] = None
    if 'channel_name' not in st.session_state:
        st.session_state['channel_name'] = 'Fireship'
    if 'format_type' not in st.session_state:
        st.session_state['format_type'] = 'code_report'
    if 'demo_mode' not in st.session_state:
        st.session_state['demo_mode'] = False

initialize_session_state()


# =============================================================================
# SIDEBAR CONFIGURATION 
# =============================================================================

with st.sidebar:
    st.header("Configuration")
    
    # OpenAI API Key Input
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=st.session_state['api_key'],
        help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys",
        placeholder="sk-..."
    )
    
    # Store in session state
    if api_key:
        st.session_state['api_key'] = api_key
        st.success("API Key provided")
    else:
        st.warning("API Key required")
    
    st.divider()
    
    # Channel Selector
    channel_name = st.selectbox(
        "Channel",
        options=["Fireship"],
        index=0,
        help="Select the YouTube channel style for brand voice"
    )
    st.session_state['channel_name'] = channel_name
    
    # Video Format Selector
    format_options = {
        "code_report": "Standard 4-5 min video [DEFAULT]",
        "100_seconds": "Quick 100-second format",
        "tutorial": "Educational deep-dive"
    }
    
    format_type = st.selectbox(
        "Video Format",
        options=list(format_options.keys()),
        format_func=lambda x: format_options[x],
        index=0,
        help="Select the script format type"
    )
    st.session_state['format_type'] = format_type
    
    st.divider()
    
    # Demo Mode Toggle
    demo_mode = st.checkbox(
        "Demo Mode",
        value=st.session_state['demo_mode'],
        help="Use cached data for faster/reliable testing"
    )
    st.session_state['demo_mode'] = demo_mode
    
    if demo_mode:
        st.info("Demo mode: Using cached HackerNews data")
    
    st.divider()
    
    # Project Info
    with st.expander("About This Project"):
        st.markdown("""
        **Script Automation Ai**
        
        A multi-agent system that uses LangGraph orchestration to:
        - Research trending tech topics
        - Generate YouTube scripts
        - Validate brand voice compliance
        - Self-correct until quality threshold met
        
        **Tech Stack:**
        - Python 3.8+
        - LangGraph for orchestration
        - OpenAI GPT-4.1 / GPT-4.1-mini
        - HackerNews API for trending topics
        
        **Workflow:**
        1. Scout Agent: Researches topic
        2. Writer Agent: Generates script
        3. Validator Agent: Scores brand voice
        4. Refinement loop if score < 75/100
        """)


# =============================================================================
# MAIN APP HEADER 
# =============================================================================

st.title("Content Automation")
st.subheader("Multi-Agent LangGraph Orchestration")
st.markdown("---")


# =============================================================================
# TWO-COLUMN LAYOUT 
# =============================================================================

col_input, col_output = st.columns([1, 1])


# =============================================================================
# INPUT COLUMN 
# =============================================================================

with col_input:
    st.header("Input")
    
    # Topic Selection Radio
    topic_mode = st.radio(
        "Topic Selection",
        options=["Auto-Discover Trending Topic", "Manual Topic Input"],
        index=0,
        help="Choose how to select the topic"
    )
    
    # Show info for auto-discover
    if topic_mode == "Auto-Discover Trending Topic":
        st.info("Will scrape HackerNews for trending tech topics")
        topic = None
    else:
        # Manual topic input
        topic = st.text_input(
            "Enter Topic",
            placeholder="e.g., React 19 Server Components",
            help="Provide a specific topic to research and write about"
        )
    
    st.markdown("---")
    
    # Generate Script Button
    generate_button = st.button(
        "Generate Script",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state['api_key']
    )
    
    if not st.session_state['api_key']:
        st.error("Please provide an API key in the sidebar")


# =============================================================================
# OUTPUT COLUMN 
# =============================================================================

with col_output:
    st.header("Output")
    
    # Status container
    status_container = st.container()
    
    # Results container
    results_container = st.container()


# =============================================================================
# WORKFLOW EXECUTION 
# =============================================================================

if generate_button:
    # Validate inputs
    if not st.session_state['api_key']:
        st.error("API Key is required. Please enter it in the sidebar.")
        st.stop()
    
    if topic_mode == "Manual Topic Input" and not topic:
        st.error("Please enter a topic or switch to Auto-Discover mode.")
        st.stop()
    
    # Show execution in status container
    with status_container:
        st.info("Starting workflow...")
        
        # Create progress tracking
        progress_bar = st.progress(0, text="Initializing...")
        status_text = st.empty()
        
        try:
            # Initialize OpenAI client with user's API key
            client = OpenAIClient(api_key=st.session_state['api_key'])
            
            # Progress updates
            progress_bar.progress(10, text="Initializing OpenAI client...")
            
            # Execute workflow with progress updates
            with st.spinner("Running multi-agent workflow..."):
                # Update progress for Scout stage
                progress_bar.progress(25, text="Scout Agent: Researching topic...")
                status_text.text("Phase 1/3: Research")
                
                # Start workflow (this will take time)
                result = run_workflow(
                    topic=topic,
                    format_type=st.session_state['format_type'],
                    channel_name=st.session_state['channel_name'],
                    demo_mode=st.session_state['demo_mode'],
                    openai_client=client
                )
                
                # Update progress for completion
                progress_bar.progress(100, text="Workflow complete!")
            
            # Store result in session state
            st.session_state['last_result'] = result
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Success message
            st.success(
                f"Script Generated Successfully! Brand Voice Score: {result.get('brand_score', 0)}/100"
            )
        
        except FileNotFoundError as e:
            # Error handling for missing config
            st.error(f"Configuration Error: {str(e)}")
            st.info("Verify that the brand voice config file exists in the config/ directory")
            st.stop()
        
        except ValueError as e:
            # Error handling for invalid inputs
            st.error(f"Invalid Input: {str(e)}")
            st.stop()
        
        except Exception as e:
            # General error handling
            st.error(f"Error: {str(e)}")
            
            with st.expander("Show full error details"):
                st.exception(e)
            
            st.info("""
            **Troubleshooting Tips:**
            - Check that your OpenAI API key is valid
            - Verify you have internet connection
            - Try enabling Demo Mode for cached data
            - Check the brand voice config file exists
            """)
            st.stop()


# =============================================================================
# RESULTS DISPLAY 
# =============================================================================

# Display results if available in session state
if st.session_state['last_result']:
    result = st.session_state['last_result']
    
    with results_container:
        st.markdown("---")
        
        # Success Banner (already shown above in workflow execution)
        
        # Metadata Metrics
        st.subheader("Execution Summary")
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("Topic", result.get('topic', 'N/A'))
        
        with metric_col2:
            st.metric("Format", result.get('format_type', 'N/A'))
        
        with metric_col3:
            st.metric("Iterations", result.get('iteration', 0))
        
        st.markdown("---")
        
        # Validation Scores
        st.subheader("Validation Scores")
        
        score_col1, score_col2, score_col3 = st.columns(3)
        
        with score_col1:
            st.metric(
                "Heuristic Score",
                f"{result.get('heuristic_score', 0)}/100"
            )
        
        with score_col2:
            st.metric(
                "LLM Score",
                f"{result.get('llm_score', 0)}/100"
            )
        
        with score_col3:
            final_score = result.get('brand_score', 0)
            st.metric(
                "Final Score",
                f"{final_score}/100",
                delta="PASSED" if final_score >= 75 else "NEEDS IMPROVEMENT"
            )
        
        st.markdown("---")
        
        # Validation Feedback
        st.subheader("Validation Feedback")
        
        feedback_col1, feedback_col2, feedback_col3 = st.columns(3)
        
        with feedback_col1:
            if result.get('validation_strengths'):
                st.markdown("**Strengths:**")
                for strength in result['validation_strengths']:
                    st.markdown(f"- {strength}")
            else:
                st.info("No strengths data available")
        
        with feedback_col2:
            if result.get('validation_weaknesses'):
                st.markdown("**Weaknesses:**")
                for weakness in result['validation_weaknesses']:
                    st.markdown(f"- {weakness}")
            else:
                st.info("No weaknesses data available")
        
        with feedback_col3:
            if result.get('validation_suggestions'):
                st.markdown("**Suggestions:**")
                for suggestion in result['validation_suggestions']:
                    st.markdown(f"- {suggestion}")
            else:
                st.info("No suggestions available")
        
        st.markdown("---")
        
        # Final Script
        st.subheader("Final Script")
        
        if result.get('final_script'):
            # Display script in markdown
            st.markdown(result['final_script'])
            
            st.markdown("---")
            
            #  Download Button
            st.download_button(
                label="Download Script (.md)",
                data=result['final_script'],
                file_name=f"{result.get('topic', 'script').replace(' ', '_')}_script.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.warning("No script generated")
        
        # Show errors if any
        if result.get('errors'):
            st.markdown("---")
            st.error("Errors encountered during execution:")
            for error in result['errors']:
                st.markdown(f"- {error}")


# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.caption("Content Video Prototype | Multi-Agent LangGraph Orchestration")

