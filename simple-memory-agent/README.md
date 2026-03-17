# Memory-Enabled Agent Lab

This lab demonstrates a production-ready conversational agent with semantic memory using:
- **Mem0** - Memory framework with semantic storage
- **Strands SDK** - Agent orchestration with tools
- **LiteLLM** - Universal LLM interface (supports any provider)
- **HuggingFace** - Text embeddings (MiniLM)
- **Qdrant** - Local vector database

## Quick Start

### 1. Get API Keys

You'll need two API keys for this lab:

#### A. Mem0 API Key (Required - FREE)

**Mem0 provides cloud memory storage for your agent.**

1. Visit https://app.mem0.ai/dashboard
2. Sign up for a free account (no credit card required)
3. Copy your API key from the dashboard
4. Add it to your `.env` file as `MEM0_API_KEY=your-key-here`

#### B. LLM Provider API Key (Required)

**Default (pre-configured):** This lab uses **Anthropic Claude Haiku 4.5** by default.

**Students can use ANY LLM provider** by setting the appropriate environment variable:
- **Anthropic** (default): https://console.anthropic.com/
- **Groq** (FREE, no credit card): https://console.groq.com/
- **OpenAI**: https://platform.openai.com/
- **Google Gemini**: https://aistudio.google.com/

The agent uses LiteLLM, which automatically detects and works with any provider!

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys:
#   - MEM0_API_KEY (required - get free at https://app.mem0.ai/dashboard)
#   - ANTHROPIC_API_KEY, GROQ_API_KEY, etc. (choose one LLM provider)
```

**Note:** The `.env` file already contains an Anthropic key for the lab. Students can replace it with their preferred provider (e.g., Groq is FREE!).

### 4. Run the Demo Agent

```bash
uv run python agent.py
```

This runs a complete demo showing:
- Automatic memory storage across conversation turns
- Semantic search when recalling information
- Explicit memory insertion for important facts
- Agent deciding when to search memory intelligently

**Note:** These validation errors have been suppressed in the code. See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for technical details about the Mem0 1.x bug.

Watch how the agent remembers your name, occupation, preferences, and project details across multiple conversation turns!

## What to Do Next

See [EXERCISE.md](EXERCISE.md) for:
- How the system works (architecture and key concepts)
- Your lab tasks (extend the agent with new capabilities)
- Test scenarios to run
- Deliverables and grading

## Technology Stack

- **LiteLLM**: Universal LLM interface supporting any provider (Anthropic, Groq, OpenAI, Gemini, etc.)
- **Anthropic Claude Haiku 4.5**: Default LLM (students can use any provider - Groq is FREE!)
- **Mem0**: Semantic memory management framework
- **Strands SDK**: Agent framework with tool support
- **HuggingFace**: Free embeddings (all-MiniLM-L6-v2)
- **Qdrant**: Local vector database (data stored in `./qdrant_data/`)

Most tools are open-source and run locally. Students can use any LLM provider they prefer!

## Need Help?

- Check `agent.py` to see the implementation
- Review EXERCISE.md for detailed explanations
- Memory data is stored in `./qdrant_data/` directory
- Logs show memory operations in real-time

## Customization

### System Prompt

The agent's system prompt is stored in `prompts/system_prompt.txt` and can be edited to customize the agent's behavior. This file explains:
- Memory capabilities
- Available tools (search_memory, insert_memory, web_search)
- When to use each tool

Edit this file to modify how the agent uses its tools without changing code.

## Quick Reference

```bash
# Run demo
uv run python agent.py

# Check dependencies
uv pip list | grep -E "mem0|strands|litellm"

# Clear memory database
rm -rf qdrant_data/

# View/edit system prompt
cat prompts/system_prompt.txt

# View environment
cat .env
```

## Switching LLM Providers

To use a different LLM provider, simply:

1. Set the appropriate API key in `.env`:
   ```bash
   # Default: Anthropic (already configured)
   ANTHROPIC_API_KEY=your-key-here

   # Alternative: Groq (FREE, no credit card required)
   GROQ_API_KEY=your-key-here

   # Alternative: OpenAI
   OPENAI_API_KEY=your-key-here

   # Alternative: Gemini
   GEMINI_API_KEY=your-key-here
   ```

2. Update the model in `agent.py` (line 48):
   ```python
   DEFAULT_MODEL: str = "claude-haiku-4-5-20251001"       # Anthropic (default)
   DEFAULT_MODEL: str = "groq/llama-3.3-70b-versatile"    # Groq (FREE)
   DEFAULT_MODEL: str = "gpt-4o-mini"                     # OpenAI
   DEFAULT_MODEL: str = "gemini/gemini-pro"               # Gemini
   ```

LiteLLM will automatically route requests to the correct provider!
