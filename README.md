# AI Agent Labs

This repository contains hands-on labs teaching production-ready patterns for building AI agents. Learn agent memory management, observability, and tool integration using modern frameworks and best practices.

## Available Labs

### 1. Agent Memory Patterns
Learn production-ready memory management for AI agents using Mem0 Cloud, Strands SDK, and semantic search.

**Points**: 100

**What You'll Learn**:
- Semantic memory with Mem0 Cloud
- Tool-based agent patterns with Strands SDK
- Automatic vs explicit memory storage
- Cross-session memory recall
- Production-ready memory architectures

### 2. Agent Observability with OpenTelemetry
Build an agent with comprehensive observability using Braintrust, OpenTelemetry, and understand GenAI metrics.

**Points**: 100 (50 required + 50 optional)

**What You'll Learn**:
- OpenTelemetry for AI agents
- Braintrust observability platform
- GenAI semantic conventions and metrics
- Tracing agent operations, tool calls, and LLM interactions
- Optional: MCP (Model Context Protocol) server integration

## Overview

Modern AI agents require robust patterns for memory, observability, and tool integration. These labs teach you production-ready approaches using established frameworks rather than building from scratch.

## Lab Structure

### Lab 1: Simple Memory Agent (100 points)

**Directory**: [simple-memory-agent/](simple-memory-agent/) | **Exercise**: [EXERCISE.md](simple-memory-agent/EXERCISE.md)

Build a memory-enabled agent using Mem0 Cloud, Strands SDK, and Anthropic Claude. This lab demonstrates production-ready memory patterns with automatic conversation storage and semantic search capabilities.

**Architecture**:
```
User Input → Mem0 Cloud (automatic storage) → Agent (Strands SDK)
                                                ├── Tool: search_memory()
                                                └── Tool: insert_memory()
Agent Response → Mem0 Cloud (automatic storage) → User
```

**Key Learning Objectives**:
- Using Mem0 for semantic memory management
- Building tool-based agents with Strands SDK
- Understanding automatic vs explicit memory storage
- Implementing memory search with semantic similarity
- Designing agents that decide when to recall information
- Production-ready memory architectures

**Technologies**:
- **Mem0 Cloud**: Semantic memory framework (cloud-hosted)
- **Strands SDK**: Agent orchestration with tool support
- **Anthropic Claude**: Haiku model via direct API

### Lab 2: Simple Agent Observability (100 points)

**Directory**: [simple-agent-observability/](simple-agent-observability/) | **Exercise**: [EXERCISE.md](simple-agent-observability/EXERCISE.md)

Build an agent with comprehensive observability using Braintrust and OpenTelemetry. Learn to trace agent operations, analyze metrics, and understand production monitoring for AI systems.

**Architecture**:
```
User Input → Agent (Strands SDK)
              ├── Tool: DuckDuckGo Search
              ├── Optional: MCP Server (Context7)
              └── Model: Anthropic Claude Haiku
                    ↓
           OpenTelemetry Traces
                    ↓
           Braintrust Dashboard
              ├── Traces & Spans
              ├── Token Usage Metrics
              └── Latency Analytics
```

**Key Learning Objectives**:
- Setting up OpenTelemetry for AI agents
- Understanding GenAI semantic conventions
- Analyzing traces, spans, and metrics in Braintrust
- Monitoring token usage and latency
- Optional: Integrating MCP (Model Context Protocol) servers
- Production observability patterns

**Technologies**:
- **Strands SDK**: Agent orchestration
- **Braintrust**: Observability platform (free tier)
- **OpenTelemetry**: Tracing and metrics
- **Anthropic Claude**: Haiku model via direct API
- **DuckDuckGo**: Web search tool
- **Optional MCP**: Model Context Protocol for documentation search

## Prerequisites

### For Lab 1 (Memory Agent)
- Python 3.11+
- Anthropic API key: https://console.anthropic.com/
- Mem0 cloud account (free tier): https://app.mem0.ai/

### For Lab 2 (Observability)
- Python 3.11+
- Anthropic API key: https://console.anthropic.com/
- Braintrust account (free tier): https://www.braintrust.dev/

## Quick Start

### 1. Install uv (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 2. Clone and Install Dependencies

```bash
cd agents-memory
uv sync
```

### 3. Lab 1 - Agent Memory

1. Get API keys:
   - Anthropic: https://console.anthropic.com/
   - Mem0 cloud: https://app.mem0.ai/
2. Configure:
   ```bash
   cd simple-memory-agent
   cp .env.example .env
   # Edit .env and add:
   #   ANTHROPIC_API_KEY
   #   MEM0_API_KEY
   ```
3. Run:
   ```bash
   uv run python agent.py
   ```
4. Complete: [simple-memory-agent/EXERCISE.md](simple-memory-agent/EXERCISE.md)

### 4. Lab 2 - Agent Observability

1. Get free API keys:
   - Anthropic: https://console.anthropic.com/
   - Braintrust: https://www.braintrust.dev/
2. Configure:
   ```bash
   cd simple-agent-observability
   cp .env.example .env
   # Edit .env and add:
   #   ANTHROPIC_API_KEY
   #   BRAINTRUST_API_KEY
   #   BRAINTRUST_PROJECT
   ```
3. Run:
   ```bash
   uv run python agent.py
   ```
4. Complete: [simple-agent-observability/EXERCISE.md](simple-agent-observability/EXERCISE.md)

## Project Structure

```
agents-memory/
├── README.md                              # This file
├── pyproject.toml                         # Shared dependencies
│
├── simple-memory-agent/                   # Lab 1: Memory (100 points)
│   ├── EXERCISE.md                        # Lab 1 instructions
│   ├── README.md                          # Technical documentation
│   ├── agent.py                           # Memory-enabled agent
│   └── .env.example                       # Environment template
│
└── simple-agent-observability/            # Lab 2: Observability (100 points)
    ├── EXERCISE.md                        # Lab 2 instructions
    ├── README.md                          # Setup and usage guide
    ├── architecture.md                    # OTEL and GenAI semantics
    ├── agent.py                           # Agent with observability
    └── .env.example                       # Environment template
```

## Key Concepts

### Automatic vs Explicit Memory

**Automatic Storage**: Every conversation turn is stored in Mem0 Cloud
- User messages stored automatically
- Agent responses stored automatically
- Background process, transparent to user
- Always available for semantic search
- Persists across sessions

**Explicit Storage**: Agent deliberately stores information
- When user says "remember this"
- When agent identifies key facts or preferences
- Uses `insert_memory` tool
- Can include metadata and tags

### Semantic Search

Mem0 Cloud uses embeddings to find relevant memories by meaning, not just keywords:

```
User: "What's my job?"
↓
Query embedding: [0.2, -0.1, 0.5, ...]
↓
Compare to all memory embeddings
↓
Top match: "Alice is a software engineer" (similarity: 0.89)
```

This enables natural, intelligent memory recall.

### When to Search Memory

The agent decides when to search based on:
- User asks about past conversations
- Question could benefit from historical context
- Proactive recall could improve response quality

This decision-making is key to intelligent memory systems.

## Grading

### Lab 1: Simple Memory Agent (100 points)

**Deliverables**:
- [ ] Completed code with new capability (40 points)
- [ ] Test output files demonstrating memory behavior (40 points)
- [ ] Brief report on memory patterns (20 points)

See [simple-memory-agent/EXERCISE.md](simple-memory-agent/EXERCISE.md) for detailed requirements.

### Lab 2: Simple Agent Observability (100 points)

**Problem 1 (Required - 50 points)**:
- [ ] Run agent with 3+ questions (10 points)
- [ ] Braintrust screenshots (15 points)
- [ ] analysis.md with trace and metrics analysis (25 points)

**Problem 2 (Optional - 50 points)**:
- [ ] MCP server integration (25 points)
- [ ] MCP testing with screenshots (10 points)
- [ ] Implementation documentation (15 points)

See [simple-agent-observability/EXERCISE.md](simple-agent-observability/EXERCISE.md) for detailed requirements.


## Troubleshooting

### Anthropic API Key Issues

```bash
ValueError: API key required
```

**Solution**: Set `ANTHROPIC_API_KEY` in `.env` file

### Mem0 Cloud Connection Issues

Verify your Mem0 API key is set correctly in `.env`:
```bash
echo $MEM0_API_KEY
```

Check Mem0 cloud service status at: https://status.mem0.ai/

## Resources

### Documentation
- [Mem0 Documentation](https://docs.mem0.ai/)
- [Strands SDK Documentation](https://github.com/awslabs/strands)
- [Anthropic Claude Documentation](https://docs.anthropic.com/)

### Learning Resources
- [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) - Anthropic's guide
- [Memory in LLM Agents](https://lilianweng.github.io/posts/2023-06-23-agent/) - Lilian Weng's blog
- [Sentence Transformers](https://www.sbert.net/) - Embedding models

## Next Steps

After completing this lab:
- Explore advanced memory patterns (summarization, consolidation)
- Build multi-agent systems with shared memory
- Integrate memory patterns in your own production agents
- Explore Mem0 cloud features for enterprise deployments

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Consult the [simple-memory-agent/README.md](simple-memory-agent/README.md) technical docs
3. Check Mem0 and Strands SDK documentation

## License

This educational material is provided for learning purposes. See individual dependencies for their licenses.
