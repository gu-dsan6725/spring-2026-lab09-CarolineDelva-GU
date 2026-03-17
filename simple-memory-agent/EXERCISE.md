# Simple Memory Agent - Lab Exercises

## Overview

This lab contains exercises to help you understand multi-tenant memory systems and implement production-ready web APIs with memory. You will first run and understand the demo agent, then convert it into a FastAPI application with user isolation and multi-session tracking.

## Reference Implementation

Before starting Problem 2, review the `streaming-stock-agent` example from the `advanced-agentic-patterns` lab:
- **Key concepts**: FastAPI setup, Server-Sent Events (SSE) streaming, Pydantic models, endpoint design

---

## Problem 1: Understanding the Memory Agent (30 Points)

### Objective

Run the demo agent to understand how semantic memory works across a conversation. The agent demonstrates different types of memory (factual, semantic, preference, episodic) within a single conversation session.

### What is agent.py?

The `agent.py` file contains a **pre-programmed demonstration** with a canned conversation between a user (Alice) and the agent. This is **not** an interactive chat - it's a scripted demo designed to showcase different memory capabilities:

1. **Turn 1-2**: Alice introduces herself and shares project information (factual + semantic memory)
2. **Turn 3**: Tests memory recall - agent retrieves name and occupation
3. **Turn 4**: Explicit memory insertion - Alice states preferences
4. **Turn 5**: Tests preference retrieval - agent recalls coding preferences
5. **Turn 6**: New topic (neural networks) - no memory search needed
6. **Turn 7**: Tests episodic recall - agent remembers the ML project

**All of this happens in ONE session** (you'll see a session ID like `75c52f1d` in the logs), demonstrating how the memory system:
- Automatically stores conversations in the background
- Semantically searches when needed
- Explicitly stores important information via tool calls
- Recalls context across multiple conversation turns

### Requirements

#### 1. Run the Agent Demo

Execute the agent and capture its output to a log file:

```bash
uv run python agent.py 2>&1 | tee agent_output.log
```

**What this does:**
- `uv run python agent.py` - Runs the demo agent
- `2>&1` - Redirects both stdout and stderr to capture all output
- `| tee agent_output.log` - Displays output on screen AND saves to file

The demo takes about 30-60 seconds to complete.

#### 2. Analyze Output and Write Explanation

**⚠️ ACADEMIC INTEGRITY REQUIREMENT:**

You MUST write your explanation document **yourself** - no AI use please. This is an analysis exercise to ensure you understand the system. AI-generated submissions will receive a zero.

**Task:** Create a file named `agent_output_explanation.md` analyzing your `agent_output.log`.

**What to include in your explanation:**

1. **Session Information** - Identify and explain the user_id, agent_id, and run_id
2. **Memory Types** - Find and categorize examples of:
   - Factual memory (personal facts: name, occupation, etc.)
   - Semantic memory (knowledge/concepts learned)
   - Preference memory (likes/dislikes, coding preferences)
   - Episodic memory (specific events/projects recalled)
3. **Tool Usage Patterns** - When does the agent use `insert_memory` tool vs. automatic background storage?
4. **Memory Recall** - Which turns trigger memory search? How do you know?
5. **Single Session** - Explain how all 7 turns happen in ONE session and why that matters

**Hints:**
- Look for patterns in which turns show "Tool #X: insert_memory"
- Compare turns 3, 5, 7 - what do they have in common?
- Check the "Memory Statistics" section at the end
- Notice when the agent's response changes based on previous turns
- Trace a single piece of information (like "Alice") through multiple turns

#### 3. Commit Your Work

Commit both files to prove you completed the exercise:

```bash
git add agent_output.log agent_output_explanation.md
git commit -m "Problem 1: Memory agent demo and analysis"
```

### Deliverables (30 Points)

**Required files (both must be committed to git):**

1. **agent_output.log** (10 points)
   - Shows successful execution of demo
   - Contains all 7 conversation turns
   - Includes memory statistics at end

2. **agent_output_explanation.md** (20 points)
   - Written by YOU (not AI-generated) ⚠️
   - Analyzes the log file with specific examples
   - Identifies all 4 memory types with quotes from output
   - Explains tool usage patterns
   - Demonstrates understanding of single-session behavior

### Evaluation Criteria

**Execution (10 points):**
- ✅ `agent_output.log` exists and shows complete demo (all 7 turns) - 5 pts
- ✅ Log shows initialization with user_id, agent_id, session_id - 3 pts
- ✅ Log includes memory statistics - 2 pts

**Analysis (20 points):**
- **Thoroughness** (10 pts): Covers all required topics (session info, memory types, tool usage, recall patterns, single-session concept)
- **Specificity** (6 pts): Cites specific examples/quotes from output, includes line numbers or turn numbers
- **Understanding** (4 pts): Explanations show genuine comprehension, written in student's own words (not AI-generated)

**Academic Integrity:**
- AI-generated submissions = **0 points** for analysis portion
- We can detect AI writing patterns - don't risk it
- This is about YOUR learning and understanding

---

## Problem 2: FastAPI Agent Application (70 Points)

### Objective

Create a FastAPI wrapper (`agent_api.py`) on top of the existing `agent.py`. The wrapper provides REST endpoints while importing and using the `Agent` class from `agent.py`. Demonstrate multi-tenant memory isolation and multi-session tracking by showing two users (Alice and Carol) interacting with the agent in different sessions.

### Reference Code

**Look at the `advanced-agentic-patterns` lab** for FastAPI implementation patterns in `streaming-stock-agent`:
- FastAPI application structure
- Server-Sent Events (SSE) for streaming responses
- Pydantic request/response models
- Endpoint design

### Requirements

#### 1. Create `agent_api.py`

Create a FastAPI wrapper that imports the `Agent` class from `agent.py` and exposes these endpoints:

##### `/ping` (GET)
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "Memory Agent API is running"
}
```

##### `/invocation` (POST)
Main conversation endpoint. Takes user query and returns agent response.

**Request Parameters:**
- `user_id` (string, required) - User identifier for memory isolation
- `run_id` (string, optional) - Session ID (auto-generate if not provided)
- `query` (string, required) - User's message
- `metadata` (dict, optional) - Additional context/tags

**Response:**
Should stream or return the agent's response.

**Implementation Hints:**

Your `agent_api.py` should follow this structure:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from agent import Agent  # Import Agent class from agent.py

app = FastAPI(
    title="Memory Agent API",
    description="Multi-tenant conversational agent with semantic memory",
    version="1.0.0"
)

# Session cache: run_id -> Agent instance
# ONE Agent per session (run_id) maintained in memory
_session_cache: Dict[str, Agent] = {}

def _get_or_create_agent(user_id: str, run_id: str) -> Agent:
    """Get existing Agent for session or create new one."""
    if run_id in _session_cache:
        return _session_cache[run_id]

    # Create new agent for this session
    agent = Agent(user_id=user_id, run_id=run_id, api_key=api_key)
    _session_cache[run_id] = agent
    return agent

# Define Pydantic request/response models here
# Implement /ping and /invocation endpoints
```

**Key Design Points:**
- Import `Agent` from `agent.py` - don't reimplement it
- Maintain session cache: ONE Agent instance per `run_id`
- Reuse the same Agent for multiple turns within a session
- Pass `user_id` and `run_id` to Agent constructor
- Extract clean response text from Agent output

#### 2. Demonstrate Multi-Tenant Isolation

Create two conversation files showing different users:

##### `alice_output.txt`

**Session 1 (5 utterances in SAME session):**

Create Alice's first session with 5 conversation turns. Here's the pattern for Turn 1:

```bash
echo "=== Alice Session 1 ===" > alice_output.txt
echo "" >> alice_output.txt

# Turn 1
echo "User: Hi, I'm Alice. I'm a software engineer." >> alice_output.txt
response=$(curl -s -X POST http://127.0.0.1:9090/invocation \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "run_id": "alice-session-1",
    "query": "Hi, I'\''m Alice. I'\''m a software engineer."
  }' | jq -r '.response')
echo "Agent: $response" >> alice_output.txt
echo "" >> alice_output.txt
```

**Write the remaining 4 turns yourself** using the same pattern with these queries:
- Turn 2: "I prefer Python for development."
- Turn 3: "What programming languages do I like?"
- Turn 4: "I'm working on a FastAPI project."
- Turn 5: "What have we discussed so far?"

Expected conversation flow:
```
User: Hi, I'm Alice. I'm a software engineer.
Agent: Hello Alice! Nice to meet you...

User: I prefer Python for development.
Agent: Got it! I'll remember that you prefer Python...

User: What programming languages do I like?
Agent: You prefer Python for development...

User: I'm working on a FastAPI project.
Agent: That's great! FastAPI is excellent for Python...

User: What have we discussed so far?
Agent: We've talked about your role as a software engineer, your preference for Python, and your FastAPI project...
```

**Session 2 (different run_id, same user_id):**

Start a NEW session (different `run_id`) to demonstrate cross-session memory recall. Here's the pattern for Turn 1:

```bash
echo "" >> alice_output.txt
echo "=== Alice Session 2 (New Session) ===" >> alice_output.txt
echo "" >> alice_output.txt

# Turn 1
echo "User: What do you remember about me?" >> alice_output.txt
response=$(curl -s -X POST http://127.0.0.1:9090/invocation \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "run_id": "alice-session-2",
    "query": "What do you remember about me?"
  }' | jq -r '.response')
echo "Agent: $response" >> alice_output.txt
echo "" >> alice_output.txt
```

**Write Turn 2 yourself** using the same pattern:
- Turn 2: "What project am I working on?"

**Note:** Use `run_id: "alice-session-2"` (different from session 1) but same `user_id: "alice"`.

Expected conversation flow:
```
User: What do you remember about me?
Agent: You're Alice, a software engineer who prefers Python...

User: What project am I working on?
Agent: You mentioned working on a FastAPI project...
```

##### `carol_output.txt`

**Session 1 (Carol's separate session):**

Create Carol's session to demonstrate user isolation. Here's the pattern for Turn 1:

```bash
echo "=== Carol Session 1 ===" > carol_output.txt
echo "" >> carol_output.txt

# Turn 1
echo "User: Hi, I'm Carol. I'm a data scientist." >> carol_output.txt
response=$(curl -s -X POST http://127.0.0.1:9090/invocation \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "carol",
    "run_id": "carol-session-1",
    "query": "Hi, I'\''m Carol. I'\''m a data scientist."
  }' | jq -r '.response')
echo "Agent: $response" >> carol_output.txt
echo "" >> carol_output.txt
```

**Write the remaining 2 turns yourself** using the same pattern:
- Turn 2: "What programming languages do I like?"
- Turn 3: "Do you know what Alice prefers?"

**Note:** Use `user_id: "carol"` (different from Alice) to demonstrate user isolation.

Expected conversation flow:
```
User: Hi, I'm Carol. I'm a data scientist.
Agent: Hello Carol! Nice to meet you...

User: What programming languages do I like?
Agent: I don't have any information about your programming language preferences yet...

User: Do you know what Alice prefers?
Agent: I don't have information about other users...
```

**Key Demonstration:**
- Carol asks "What programming languages do I like?"
- Agent should respond "I don't know" or "I don't have information yet"
- **NOT** use Alice's memory (proves user isolation)

#### 3. Output Format

**Important:** The output files should contain **ONLY** user and agent conversation:
- ✅ Show: `User: ...` and `Agent: ...`
- ❌ Don't show: Log messages, tool calls, debug info, timestamps

**Clean format example:**
```
User: Hi, I'm Alice.
Agent: Hello Alice! Nice to meet you. How can I help you today?

User: I prefer Python.
Agent: Got it! I'll remember that you prefer Python.
```

### Deliverables

**Required files to commit:**

1. **agent_api.py** - FastAPI application with `/ping` and `/invocation` endpoints
2. **alice_output.txt** - Alice's conversations (Session 1: 5 utterances, Session 2: follow-up questions)
3. **carol_output.txt** - Carol's conversation demonstrating user isolation

**Optional (recommended):**
- Shell scripts (e.g., `alice_session1.sh`, `alice_session2.sh`, `carol_session1.sh`) to automate testing
- These scripts make it easy to regenerate output files and verify behavior

### Testing Your Implementation

#### Step 1: Kill Any Previous Running Instances

Before starting a fresh server, kill any existing instances:

```bash
# Kill any running agent_api servers
pkill -f "uvicorn agent_api:app" || true
```

#### Step 2: Start the Server

```bash
# Start the FastAPI server on port 9090
uv run uvicorn agent_api:app --reload --host 127.0.0.1 --port 9090
```

The server will start and display:
```
INFO:     Uvicorn running on http://127.0.0.1:9090 (Press CTRL+C to quit)
```

#### Step 3: Test Health Check

In a new terminal, test the /ping endpoint:

```bash
curl http://127.0.0.1:9090/ping
```

Expected response:
```json
{"status":"ok","message":"Memory Agent API is running"}
```

#### Step 4: Generate Alice's Conversations

You can run the curl commands directly or create shell scripts for automation.

**Option A: Run curl commands manually** (following the patterns from section 2)

**Option B: Create and run shell scripts** (recommended for automation):

```bash
# Session 1: 5 utterances
./alice_session1.sh

# Session 2: Cross-session memory test
./alice_session2.sh

# View Alice's complete output
cat alice_output.txt
```

#### Step 5: Generate Carol's Conversations

Similarly, run Carol's conversation:

```bash
# Session 1: User isolation test
./carol_session1.sh

# View Carol's output
cat carol_output.txt
```

#### Manual Testing (Optional)

You can also test individual requests manually:

**Test /invocation with Alice:**
```bash
curl -X POST http://127.0.0.1:9090/invocation \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "run_id": "session-1",
    "query": "Hi, I'\''m Alice. I'\''m a software engineer."
  }'
```

**Test /invocation with Carol (same question as Alice):**
```bash
curl -X POST http://127.0.0.1:9090/invocation \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "carol",
    "run_id": "session-1",
    "query": "What programming languages do I like?"
  }'
```

Expected: Carol should get "I don't know" response.

#### Step 6: Stop the Server

When done testing:

```bash
# Press CTRL+C in the server terminal, or:
pkill -f "uvicorn agent_api:app"
```

### What We're Testing

1. **Multi-Tenant Isolation:**
   - Alice's memories don't leak to Carol
   - Each user has separate memory space
   - Carol asking Alice's questions gets different answers

2. **Multi-Session Tracking:**
   - Alice Session 2 can recall information from Session 1
   - run_id properly tracks different conversation sessions
   - Cross-session memory retrieval works

3. **Clean Output:**
   - Output files show only user/agent conversation
   - No logs, tool calls, or debug information
   - Easy to read and verify behavior

### Evaluation Criteria (70 Points Total)

**Implementation (28 points):**
- FastAPI application with `/ping` and `/invocation` endpoints
- Proper Pydantic models for requests
- Correct parameter handling (user_id, run_id, query, metadata)
- Application runs without errors

**Multi-Tenant Isolation (21 points):**
- Alice and Carol have separate memory spaces
- Carol can't access Alice's preferences/information
- Demonstrates "I don't know" response for Carol

**Multi-Session Tracking (14 points):**
- Alice's Session 2 recalls Session 1 information
- run_id properly isolates sessions
- Cross-session memory retrieval demonstrated

**Output Quality (7 points):**
- Clean conversation format (no logs/debug info)
- All required utterances present
- Clear demonstration of memory behavior

### Tips

1. **Study the reference:** The `streaming-stock-agent` from `advanced-agentic-patterns` lab shows good FastAPI patterns
2. **Use existing code:** Import and use the `Agent` class from `agent.py`
3. **Keep it simple:** Focus on demonstrating memory isolation and tracking
4. **Test thoroughly:** Make sure Carol can't see Alice's data
5. **Clean output:** Strip logs before saving to output files

### Submission

```bash
git add agent_api.py alice_output.txt carol_output.txt
git commit -m "Problem 2: FastAPI agent with multi-tenant demo"
```

---

## Getting Help

- Review `architecture.md` for multi-tenant design principles
- Check `agent_multi_tenant.py` for multi-user patterns
- Look at the `advanced-agentic-patterns` lab and `streaming-stock-agent` for FastAPI examples
- Review Mem0 documentation: https://docs.mem0.ai/
- Check FastAPI documentation: https://fastapi.tiangolo.com/

Good luck!
