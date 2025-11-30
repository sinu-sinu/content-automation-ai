# Content Video Prototype

> A technical demonstration of multi-agent AI orchestration for automated content generation

An AI-powered YouTube script generator that uses LangGraph orchestration to create tech content in the style of popular YouTube channels.

## Overview

This is an intelligent content creation system that combines multiple AI agents to research, write, and validate YouTube scripts. It uses a self-correcting workflow that iteratively improves scripts until they meet brand voice standards.

The system can automatically discover trending topics from HackerNews, research them, generate scripts in various formats, and validate them against predefined brand voice guidelines.

## Features

- **Multi-Agent System**: Scout, Writer, and Validator agents work together through LangGraph orchestration
- **Self-Correcting Workflow**: Automatically refines scripts until they meet quality thresholds (75/100 score)
- **Trending Topic Discovery**: Scrapes HackerNews for hot tech topics
- **Multiple Script Formats**:
  - `code_report` - Typical 4-5 minute videos (default)
  - `100_seconds` - Quick 2-minute explainers
  - `tutorial` - Educational deep-dive format
- **Brand Voice Validation**: Dual scoring system (heuristic + LLM-based)
- **Demo Mode**: Uses cached data for reliable testing
- **Interactive & CLI Modes**: Flexible usage options

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key
- Virtual environment recommended

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   
   # Windows CMD
   python -m venv venv
   venv\Scripts\activate.bat
   
   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   DEMO_MODE=false
   DEBUG=true
   ```

## Usage

### Interactive Mode (Recommended)

Run without arguments for an interactive prompt:

```bash
python run.py
```

The interactive interface guides you through:
- Channel name selection
- Topic input or auto-discovery from trending tech topics
- Script format selection (quick explainer, standard, or tutorial)
- Demo mode toggle for testing

### CLI Mode

**Generate script for a specific topic:**
```bash
python run.py --topic "React 19 Server Components"
```

**Auto-discover trending topic:**
```bash
python run.py --auto
```

**Specify script format:**
```bash
python run.py --topic "Rust vs Go" --format 100_seconds
```

**Use demo mode (cached data):**
```bash
python run.py --demo --auto
```

**Specify custom channel:**
```bash
python run.py --channel YourChannel --topic "AI Trends"
```

### Command Reference

| Command | Description |
|---------|-------------|
| `python run.py` | Interactive mode |
| `python run.py --topic "X"` | Generate script for topic X |
| `python run.py --auto` | Auto-discover trending topic |
| `python run.py --demo` | Use cached data |
| `python run.py --format 100_seconds` | Quick 2-minute format |
| `python run.py --channel NAME` | Specify channel |

## Project Structure

```
electrify video prototype/
├── config/                          # Brand voice configurations
│   └── fireship_brand_voice.json   # Example channel config
├── examples/                        # Example data and outputs
│   └── cached_hn_trending.json     # Cached HackerNews data
├── src/
│   ├── agents/                     # AI agent implementations
│   │   ├── tech_scout.py           # Research agent
│   │   ├── script_writer.py        # Script generation agent
│   │   └── brand_voice.py          # Validation agent
│   ├── orchestrator/               # LangGraph workflow
│   │   └── workflow.py             # Main orchestration logic
│   └── utils/                      # Utilities
│       ├── hn_scraper.py           # HackerNews API client
│       ├── openai_client.py        # OpenAI wrapper
│       └── brand_voice_loader.py   # Config loader
├── tests/                          # Test suite
│   ├── test_workflow.py            # Core workflow tests
│   └── test_phase5.py              # Orchestration tests
├── .env                            # Environment variables (create this)
├── requirements.txt                # Python dependencies
├── run.py                          # Main entry point
├── QUICKSTART.md                   # Quick start guide
└── README.md                       # This file
```

## How It Works

### Workflow Architecture

The system follows a self-correcting LangGraph workflow:

```
1. Scout Agent
   └─> Researches topic using HackerNews API
   └─> Gathers key information, trends, and context
   
2. Writer Agent
   └─> Generates draft script based on research
   └─> Follows channel-specific format guidelines
   
3. Validator Agent
   └─> Scores script against brand voice (0-100)
   └─> Uses dual scoring: heuristic + LLM
   
4. Decision Point
   ├─> If score >= 75: DONE
   └─> If score < 75 and iteration < 2:
       └─> Refine → Validate again
       
5. Final Output
   └─> Polished script + validation feedback
```

### Agent Architecture

**Tech Scout Agent**: 
- Fetches trending topics from HackerNews API
- Filters for technical relevance using intelligent scoring
- Compiles structured research briefs with key talking points

**Script Writer Agent**: 
- Generates scripts in configurable formats (quick explainer, standard report, tutorial)
- Adapts tone and structure based on channel configuration
- Implements format-specific templates and pacing guidelines

**Brand Voice Validator**: 
- Dual-scoring system: heuristic pattern matching + LLM-based analysis
- Evaluates scripts against configurable quality thresholds
- Provides actionable feedback for iterative improvement

### Brand Voice Configuration

Each channel has a JSON configuration defining:
- Voice characteristics (tone, pacing, humor style)
- Signature phrases and patterns
- Content structure preferences
- Quality thresholds

Example: `config/fireship_brand_voice.json`

## Development & Testing

This project demonstrates proficiency in:
- Multi-agent AI system design and orchestration
- LangGraph workflow implementation
- API integration and error handling
- Self-correcting AI systems with validation loops
- Brand voice consistency and quality control

### Running Tests

```bash
# Core workflow tests
python tests/test_workflow.py

# Orchestration tests
python tests/test_phase5.py
```

### Adding a New Channel

1. Create `config/{channel_name}_brand_voice.json`
2. Use existing config files as a template
3. Define voice characteristics, patterns, and requirements
4. Run with `--channel {channel_name}`

The modular configuration system allows for easy adaptation to different content styles.

### Project Status

**Completed Phases:**
- Phase 1: OpenAI Integration
- Phase 2: Tech Scout Agent
- Phase 3: Script Writer Agent
- Phase 4: Brand Voice Validator
- Phase 5: LangGraph Orchestration

**Roadmap (Future Enhancements):**
- Phase 6: Streamlit Web Interface for non-technical users
- Phase 7: Advanced analytics and A/B testing capabilities
- Fast API integrations

## Troubleshooting

### "No module named 'src'"
- Ensure you're running from project root
- Verify virtual environment is activated

### "API key not found"
- Check `.env` file exists in project root
- Verify `OPENAI_API_KEY` is set correctly
- Test with: `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"`

### "Brand voice config not found"
- Verify the brand voice config file exists in `config/` directory
- For custom channels, ensure `config/{channel_name}_brand_voice.json` exists

### Workflow taking too long
- Use `--demo` flag for cached HackerNews data
- Check internet connection
- Verify OpenAI API is responding

## Technical Stack & Architecture

**Core Technologies:**
- **Python 3.8+**: Type-hinted, modular codebase
- **LangGraph**: State-based agent orchestration with conditional routing
- **OpenAI API**: GPT-4.1/4.1-mini for generation and validation
- **HackerNews API**: Real-time trending topic discovery
- **LangChain**: LLM utilities and prompt management

**Design Patterns:**
- Modular agent architecture with clear separation of concerns
- Configuration-driven brand voice system (JSON-based)
- State machine workflow with automatic error recovery
- Dual validation (heuristic + LLM) for quality assurance
- Caching layer for reliable testing and reduced API costs

**Scalability Features:**
- Channel-agnostic configuration system
- Pluggable agent architecture
- Format-extensible script generation
- Environment-based configuration management

## About This Project

This is a technical demonstration project showcasing:
- Advanced AI agent orchestration
- Production-quality code architecture
- Self-correcting AI workflows
- Modular, extensible system design

Built as a prototype to demonstrate capabilities in AI system design, LangGraph orchestration, and scalable content generation pipelines.

## Key Technical Highlights

This prototype demonstrates:
- **Advanced AI Orchestration**: Multi-agent system using LangGraph with conditional routing
- **Self-Healing Workflows**: Automatic script refinement based on quality scores
- **Scalable Architecture**: Modular design allowing easy addition of new channels and formats
- **Production-Ready Code**: Comprehensive error handling, testing, and documentation
- **API Integration**: External data sources (HackerNews) for dynamic content discovery