# Simple Memory Agent Architecture

## Table of Contents

1. [System Overview](#system-overview)
2. [Multi-Tenant Architecture](#multi-tenant-architecture)
3. [Overall System Architecture](#overall-system-architecture)
4. [Memory Flow Diagram](#memory-flow-diagram)
5. [Tool Pattern](#tool-pattern)
6. [Memory Types Explained](#memory-types-explained)
7. [Backend Abstraction Pattern](#backend-abstraction-pattern)
8. [Implicit vs Explicit Memory](#implicit-vs-explicit-memory)
9. [Data Flow Diagrams](#data-flow-diagrams)
10. [Implementation Details](#implementation-details)
11. [Comparison with Other Solutions](#comparison-with-other-solutions)

---

## System Overview

This system implements a conversational agent with semantic memory using:

- **Agent Framework**: Strands SDK for agent orchestration
- **Memory Framework**: Mem0 for memory management
- **Vector Database**: Qdrant for local storage
- **LLM Provider**: Groq via LiteLLM (llama-3.3-70b)
- **Embeddings**: HuggingFace (all-MiniLM-L6-v2)

Key characteristics:
- Automatic conversation storage in the background
- Semantic search across conversation history
- Tool-based explicit memory operations
- Local storage with no cloud dependencies

### File Structure

```
simple-memory-agent/
├── agent.py               # Main agent implementation
├── memory_manager.py      # Backend abstraction layer
├── prompts/               # System prompts directory
│   └── system_prompt.txt  # Agent behavior and tool usage instructions
├── qdrant_data/           # Vector database (created on first run)
├── .env                   # API keys (not in git)
└── .env.example           # Configuration template
```

**Prompts Directory**: System prompts are externalized to `prompts/system_prompt.txt` for easy modification without changing code. This file defines the agent's behavior, tool usage patterns, and response style.

---

## Multi-Tenant Architecture

### Design Principle: ONE MemoryManager for ALL Users and Sessions

The memory system is designed with a **true multi-tenant architecture** where a **single MemoryManager instance serves all users and sessions**. This is a critical design decision that enables scalable, production-ready applications.

### Architecture Pattern

```
┌──────────────────────────────────────────────────────────────────────┐
│                    MULTI-TENANT MEMORY MANAGER                        │
│                     (ONE Instance for Everyone)                       │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │         MemoryManager(model, api_key)                      │     │
│  │         - NO user_id stored                                │     │
│  │         - NO agent_id stored                               │     │
│  │         - NO run_id stored                                 │     │
│  │                                                             │     │
│  │  Methods accept context as parameters:                     │     │
│  │  - search(user_id, query, agent_id, run_id, ...)          │     │
│  │  - insert(user_id, content, agent_id, run_id, ...)        │     │
│  │  - add_conversation(user_id, user_msg, asst_msg, ...)     │     │
│  │  - get_all(user_id, ...)                                   │     │
│  │  - clear(user_id)                                          │     │
│  └────────────────────────────────────────────────────────────┘     │
│         ↓              ↓              ↓              ↓               │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐         │
│   │ User A  │    │ User B  │    │ User C  │    │ User D  │         │
│   │Session 1│    │Session 1│    │Session 1│    │Session 1│         │
│   │Session 2│    │Session 2│    │Session 2│    │Session 2│         │
│   └─────────┘    └─────────┘    └─────────┘    └─────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

### Why Multi-Tenant Architecture?

**1. Multi-Tenant Isolation**
- Each user's memories are completely isolated by `user_id`
- Multiple users can interact with the same agent application
- No data leakage between users
- Production-ready for SaaS applications

Example:
```python
# Alice's memories
await memory_manager.search(user_id="alice", query="my preferences")

# Bob's memories (completely isolated)
await memory_manager.search(user_id="bob", query="my preferences")
```

**2. Multi-Session Tracking**
- Each conversation is tagged with a unique `run_id` (session ID)
- Users can have multiple concurrent or sequential sessions
- Session history can be tracked and retrieved
- Better organization of conversation context

Example:
```python
# Alice's morning session
await memory_manager.insert(
    user_id="alice",
    content="Discussed Python project",
    run_id="morning-session-abc123"
)

# Alice's afternoon session (same user, different session)
await memory_manager.insert(
    user_id="alice",
    content="Discussed JavaScript project",
    run_id="afternoon-session-xyz789"
)
```

**3. Metadata Tagging for Enhanced Search**
- Memories are automatically tagged with session context
- `agent_id` enables multi-agent scenarios
- `run_id` tracks which session created the memory
- Additional custom metadata can be added
- Enables powerful filtering and retrieval

**IMPORTANT: Cross-Session Memory Recall**

Memory search **always retrieves from ALL sessions** for a user. The `run_id` is used when storing memories (to track which session created them) but is **NOT used when searching**. This enables cross-session memory recall - the agent can remember information from any previous conversation.

Example:
```python
# Alice in Session 1 stores a memory
await memory_manager.insert(
    user_id="alice",
    content="I prefer Python for development",
    run_id="session-1"
)

# Alice in Session 2 (different run_id) can recall it
results = await memory_manager.search(
    user_id="alice",
    query="programming preferences",
    run_id="session-2"  # Provided for context but NOT used in search
)
# Returns: "I prefer Python for development" (from session-1)

# User isolation: Bob cannot see Alice's memories
results = await memory_manager.search(
    user_id="bob",
    query="programming preferences"
)
# Returns: empty (no memories for Bob)
```

**Why not filter by run_id during search?**
- Enables the agent to remember information across sessions
- Alice's Session 2 can recall what she said in Session 1
- User isolation is handled by `user_id` alone
- `run_id` is metadata for organization, not a search filter

**4. Resource Efficiency**
- Single backend connection (Qdrant, Mem0) shared across all users
- Lower memory footprint (one instance vs. thousands)
- Simplified state management
- Better for horizontal scaling

### Implementation Details

#### MemoryManager Initialization
```python
# Initialize ONCE for the entire application
memory_manager = MemoryManager(
    model="claude-haiku-4-5-20251001",
    api_key=api_key
)
# No user context stored - this serves ALL users
```

#### Agent Integration
```python
class Agent:
    def __init__(self, user_id, agent_id=None, run_id=None):
        # Agent stores user/session context
        self.user_id = user_id
        self.agent_id = agent_id or "memory-agent"
        self.run_id = run_id or str(uuid.uuid4())[:8]

        # Uses shared multi-tenant MemoryManager
        self.memory_manager = MemoryManager(model=model, api_key=api_key)

    def chat(self, user_input):
        # Pass user/session context to memory operations
        await self.memory_manager.add_conversation(
            user_id=self.user_id,
            user_message=user_input,
            assistant_message=response,
            agent_id=self.agent_id,
            run_id=self.run_id
        )
```

#### Tool Functions
```python
def _create_search_memory_tool(memory_manager, user_id, agent_id, run_id):
    @tool
    async def search_memory(query: str, limit: int = 5) -> str:
        # Tools have user/session context captured in closure
        results = await memory_manager.search(
            user_id=user_id,
            query=query,
            limit=limit,
            agent_id=agent_id,
            run_id=run_id
        )
        return json.dumps(results)
    return search_memory
```

### Session Management

Sessions are identified by `run_id` (typically a UUID or custom identifier):

```python
import uuid

# Auto-generate session ID
agent = Agent(
    user_id="alice",
    run_id=str(uuid.uuid4())[:8]  # Short UUID: "a3b2c1d4"
)

# Or use custom session ID
agent = Agent(
    user_id="alice",
    run_id="morning-planning-2024-01-15"
)

# Start new session for same user
agent.run_id = str(uuid.uuid4())[:8]
```

### FastAPI Application Pattern

For production deployments, the multi-tenant architecture enables a single FastAPI application to serve all users:

```python
from fastapi import FastAPI

# Single MemoryManager instance at application level
memory_manager = MemoryManager(model=model, api_key=api_key)

@app.post("/invocation")
async def invoke_agent(user_id: str, run_id: str, query: str):
    # Create ephemeral agent for this request
    agent = Agent(user_id=user_id, run_id=run_id)

    # Use shared memory manager (passed via constructor)
    response = agent.chat(query)

    return {"response": response}
```

### Comparison: Multi-Tenant vs. Single-Tenant

**❌ Single-Tenant (Anti-Pattern)**
```python
# BAD: One MemoryManager per user (doesn't scale)
class Agent:
    def __init__(self, user_id):
        self.user_id = user_id
        # Creates new backend connection for EACH user
        self.memory_manager = MemoryManager(
            user_id=user_id,  # Stored in instance
            model=model,
            api_key=api_key
        )

    async def search(self, query):
        # user_id already stored, just call search
        return await self.memory_manager.search(query=query)
```

**✅ Multi-Tenant (Correct Pattern)**
```python
# GOOD: One MemoryManager for ALL users (scales)
class Agent:
    def __init__(self, user_id):
        self.user_id = user_id
        # Uses shared MemoryManager instance
        self.memory_manager = shared_memory_manager

    async def search(self, query):
        # Pass user_id as parameter for isolation
        return await self.memory_manager.search(
            user_id=self.user_id,
            query=query
        )
```

### Benefits Summary

| Feature | Single-Tenant | Multi-Tenant |
|---------|--------------|--------------|
| Users per instance | 1 | Unlimited |
| Backend connections | 1 per user | 1 total |
| Memory footprint | High (N instances) | Low (1 instance) |
| User isolation | ❌ Not needed | ✅ Built-in |
| Session tracking | ❌ No | ✅ Yes |
| Metadata filtering | ❌ Limited | ✅ Full support |
| Production-ready | ❌ No | ✅ Yes |
| Scalability | ❌ Poor | ✅ Excellent |

---

## Overall System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                              │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             │ User Input
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                        MEMORY AGENT LAYER                             │
│                                                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    Agent (Strands SDK)                        │  │
│  │                                                                │  │
│  │  Model: LiteLLMModel (Groq/llama-3.3-70b)                     │  │
│  │  System Prompt: Memory-aware instructions                     │  │
│  │                                                                │  │
│  │  Available Tools:                                              │  │
│  │  ┌─────────────────────────────────────────────────────────┐  │  │
│  │  │ search_memory(query, limit) → JSON results              │  │  │
│  │  │ insert_memory(content, metadata) → JSON status          │  │  │
│  │  └─────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                             │                                        │
│                             │ Tool Calls                             │
│                             ↓                                        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                   Memory Manager (Mem0)                       │  │
│  │                                                                │  │
│  │  Operations:                                                   │  │
│  │  - add(messages, user_id) → Store conversation                │  │
│  │  - search(query, user_id, limit) → Retrieve memories          │  │
│  │  - get_all(user_id) → Export all memories                     │  │
│  │  - delete(memory_id) → Remove specific memory                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             │ Vector Operations
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                         STORAGE LAYER                                 │
│                                                                       │
│  ┌────────────────────┐         ┌────────────────────────────────┐  │
│  │  Embedder          │         │  Vector Store                   │  │
│  │  (HuggingFace)     │────────▶│  (Qdrant)                       │  │
│  │                    │         │                                  │  │
│  │  Model:            │         │  Collection: agent_memories     │  │
│  │  all-MiniLM-L6-v2  │         │  Dimensions: 384                │  │
│  │  Dimensions: 384   │         │  Path: ./qdrant_data/           │  │
│  │                    │         │  Storage: Local disk            │  │
│  └────────────────────┘         └────────────────────────────────┘  │
│                                                                       │
│  Text → [0.23, -0.45, 0.67, ...] → Store in Qdrant with metadata    │
└───────────────────────────────────────────────────────────────────────┘
```

**Component Responsibilities:**

1. **User Interface**: Receives user input, displays responses
2. **Agent Layer**: Processes requests, decides when to use memory tools
3. **Memory Manager**: Abstracts Mem0 operations, handles storage/retrieval
4. **Storage Layer**: Converts text to embeddings, stores vectors in Qdrant

---

## Memory Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                   │
│                    "My name is Alice"                                │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Step 1: Automatic Storage
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   IMPLICIT MEMORY STORAGE                            │
│                                                                      │
│  memory.add(                                                         │
│      messages=[{"role": "user", "content": "My name is Alice"}],    │
│      user_id="default_user"                                          │
│  )                                                                   │
│                                                                      │
│  Text → Embeddings → Qdrant Vector Store                            │
│  "My name is Alice" → [0.23, -0.45, 0.67, ...] → Stored            │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Step 2: Agent Processing
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT PROCESSING                                │
│                                                                      │
│  1. Agent receives: "My name is Alice"                              │
│  2. Agent analyzes: Introduction, no history needed                 │
│  3. Decision: No search_memory tool call needed                     │
│  4. Generates response: "Nice to meet you, Alice!"                  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Step 3: Response Storage
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   IMPLICIT MEMORY STORAGE                            │
│                                                                      │
│  memory.add(                                                         │
│      messages=[{                                                     │
│          "role": "assistant",                                        │
│          "content": "Nice to meet you, Alice!"                       │
│      }],                                                             │
│      user_id="default_user"                                          │
│  )                                                                   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Step 4: Return to User
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         USER RECEIVES                                │
│                  "Nice to meet you, Alice!"                          │
└─────────────────────────────────────────────────────────────────────┘


                    LATER IN CONVERSATION
                    ─────────────────────


┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                   │
│                      "What's my name?"                               │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Step 1: Automatic Storage
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   IMPLICIT MEMORY STORAGE                            │
│  Store: "What's my name?" in Mem0                                   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Step 2: Agent Processing
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT PROCESSING                                │
│                                                                      │
│  1. Agent receives: "What's my name?"                               │
│  2. Agent analyzes: Question about past information                 │
│  3. Decision: USE search_memory tool                                │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  TOOL CALL: search_memory                                    │   │
│  │                                                               │   │
│  │  Input:                                                       │   │
│  │    query: "user's name"                                       │   │
│  │    limit: 5                                                   │   │
│  │                                                               │   │
│  │  Process:                                                     │   │
│  │    1. Convert query to embedding                             │   │
│  │    2. Search Qdrant for similar vectors                      │   │
│  │    3. Return ranked results                                  │   │
│  │                                                               │   │
│  │  Output:                                                      │   │
│  │    {                                                          │   │
│  │      "status": "success",                                     │   │
│  │      "count": 1,                                              │   │
│  │      "memories": [                                            │   │
│  │        {                                                      │   │
│  │          "memory": "My name is Alice",                        │   │
│  │          "score": 0.89,                                       │   │
│  │          "id": "mem_123"                                      │   │
│  │        }                                                      │   │
│  │      ]                                                        │   │
│  │    }                                                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  4. Agent uses result to formulate response                         │
│  5. Generates: "Your name is Alice!"                                │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         │ Step 3: Response Storage & Return
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Store response in Mem0 → Return to user                            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tool Pattern

The agent uses memory through tools, not direct access. This provides:
- Clear abstraction boundaries
- Agent decides when to use memory
- Testable, modular components

### Tool Wrapper Pattern

```
┌───────────────────────────────────────────────────────────────────┐
│                       STRANDS AGENT                                │
│                                                                    │
│  Has access to:                                                    │
│  - @tool decorated functions                                       │
│  - Function docstrings (used by LLM to decide when to call)       │
│  - Type hints (used for validation)                                │
└────────────────┬──────────────────────────────────────────────────┘
                 │
                 │ Calls tools when needed
                 ↓
┌───────────────────────────────────────────────────────────────────┐
│                     TOOL FUNCTIONS                                 │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ @tool                                                        │ │
│  │ def search_memory(query: str, limit: int = 5) -> str:      │ │
│  │     """Search for relevant information from previous         │ │
│  │     conversations using semantic search.                     │ │
│  │                                                              │ │
│  │     Use this when you need to recall specific facts,         │ │
│  │     preferences, or context from earlier conversations.      │ │
│  │     """                                                       │ │
│  │     # Call memory manager                                    │ │
│  │     results = memory.search(query, user_id, limit)          │ │
│  │     # Format and return JSON                                 │ │
│  │     return json.dumps(results)                               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ @tool                                                        │ │
│  │ def insert_memory(                                           │ │
│  │     content: str,                                            │ │
│  │     metadata: Optional[Dict[str, Any]] = None               │ │
│  │ ) -> str:                                                    │ │
│  │     """Explicitly store important information in             │ │
│  │     long-term memory.                                        │ │
│  │                                                              │ │
│  │     Use this for facts, preferences, or key information      │ │
│  │     that should be remembered across conversations.          │ │
│  │     """                                                       │ │
│  │     # Call memory manager                                    │ │
│  │     memory.add(messages=[...], user_id, metadata)           │ │
│  │     # Return JSON status                                     │ │
│  │     return json.dumps({"status": "success"})                │ │
│  └─────────────────────────────────────────────────────────────┘ │
└────────────────┬──────────────────────────────────────────────────┘
                 │
                 │ Delegates to
                 ↓
┌───────────────────────────────────────────────────────────────────┐
│                     MEMORY MANAGER (Mem0)                          │
│                                                                    │
│  memory.search(query, user_id, limit) → List[Dict]               │
│  memory.add(messages, user_id, metadata) → None                   │
│  memory.get_all(user_id) → List[Dict]                            │
│  memory.delete(memory_id) → None                                  │
└────────────────┬──────────────────────────────────────────────────┘
                 │
                 │ Uses
                 ↓
┌───────────────────────────────────────────────────────────────────┐
│               STORAGE BACKEND (Qdrant + Embeddings)               │
└───────────────────────────────────────────────────────────────────┘
```

### Tool Factory Pattern

Tools are created with closure over memory and user_id:

```python
def _create_search_memory_tool(memory: Memory, user_id: str):
    """Factory function that creates a tool with bound context."""

    @tool
    def search_memory(query: str, limit: int = 5) -> str:
        """Tool docstring visible to agent."""
        # Has access to memory and user_id from closure
        results = memory.search(
            query=query,
            user_id=user_id,  # Bound in closure
            limit=limit
        )
        return json.dumps(results)

    return search_memory


def _create_insert_memory_tool(memory: Memory, user_id: str):
    """Factory function for insert tool."""

    @tool
    def insert_memory(
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Tool docstring visible to agent."""
        # Has access to memory and user_id from closure
        memory.add(
            messages=[{"role": "user", "content": content}],
            user_id=user_id,  # Bound in closure
            metadata=metadata or {}
        )
        return json.dumps({"status": "success"})

    return insert_memory


# Usage in agent initialization:
search_tool = _create_search_memory_tool(self.memory, user_id)
insert_tool = _create_insert_memory_tool(self.memory, user_id)

self.agent = Agent(
    model=model,
    system_prompt=system_prompt,
    tools=[search_tool, insert_tool]
)
```

**Benefits of this pattern:**
1. Tools have clean signatures (no memory/user_id parameters)
2. Context is bound at creation time
3. Agent sees simple, focused tool interfaces
4. Easy to add new tools without changing agent code

---

## Memory Types Explained

### 1. Semantic Memory (Facts and Knowledge)

**Definition**: Extracted facts and structured knowledge

**Storage**:
```
User: "I'm a software engineer specializing in Python"

Mem0 extracts and stores:
- "User is a software engineer"
- "User specializes in Python"
```

**Retrieval**:
```
Query: "What's my occupation?"
Search embedding space → Find: "software engineer" (high similarity)
```

**Implementation**:
Automatic extraction by Mem0's LLM processing.

---

### 2. Episodic Memory (Conversation History)

**Definition**: Full conversation turns stored as-is

**Storage**:
```
Every chat turn:
{
    "role": "user",
    "content": "My name is Alice and I work at TechCorp"
}
{
    "role": "assistant",
    "content": "Nice to meet you, Alice! Tell me more about TechCorp."
}
```

**Retrieval**:
```
Query: "What company did I mention?"
Semantic search finds: "I work at TechCorp" conversation turn
```

**Implementation**:
```python
def chat(self, user_input: str) -> str:
    # Store user message (episodic)
    self._store_conversation_async(user_input, None)

    # Process
    response = self.agent(user_input)

    # Store assistant message (episodic)
    self._store_conversation_async(user_input, response)

    return response
```

---

### 3. User Preferences (Settings and Likes/Dislikes)

**Definition**: Explicitly stated preferences

**Storage**:
```
User: "Remember that I prefer dark mode"

Agent uses insert_memory tool:
{
    "content": "User prefers dark mode UI",
    "metadata": {
        "type": "preference",
        "category": "ui"
    }
}
```

**Retrieval**:
```
Query: "What are my UI preferences?"
Filtered search: type="preference" AND category="ui"
Returns: "User prefers dark mode UI"
```

**Implementation**:
Extension example (not in base code):
```python
@tool
def set_preference(key: str, value: str) -> str:
    """Store a user preference."""
    memory.add(
        messages=[{
            "role": "user",
            "content": f"Preference: {key}={value}"
        }],
        user_id=user_id,
        metadata={
            "type": "preference",
            "key": key,
            "value": value
        }
    )
    return json.dumps({"status": "success"})
```

---

### 4. Summary Memory (Compressed Conversations)

**Definition**: Condensed summaries of long conversations

**Storage**:
```
After 10 turns about "machine learning project":

Generate summary:
"User is building a machine learning model using scikit-learn
for customer churn prediction. Dataset has 10k rows. Currently
in feature engineering phase."

Store with metadata:
{
    "content": summary,
    "metadata": {
        "type": "summary",
        "topic": "ml_project",
        "turns_covered": 10
    }
}
```

**Retrieval**:
```
Query: "Tell me about my project"
Returns summary instead of 10 individual turns
More efficient, preserves context
```

**Implementation**:
Extension example (not in base code):
```python
@tool
def summarize_conversation(topic: str, num_turns: int = 10) -> str:
    """Create a summary of recent conversation."""
    # Search for recent memories about topic
    memories = memory.search(query=topic, limit=num_turns)

    # Use LLM to generate summary
    summary = llm.generate_summary(memories)

    # Store summary
    memory.add(
        messages=[{"role": "assistant", "content": summary}],
        user_id=user_id,
        metadata={
            "type": "summary",
            "topic": topic,
            "turns_covered": len(memories)
        }
    )

    return json.dumps({"status": "success", "summary": summary})
```

---

## Backend Abstraction Pattern

The system uses a clean abstraction to allow swapping Mem0 with other solutions.

### Current Architecture with Mem0

```
┌───────────────────────────────────────────────────────────────┐
│                      Agent Class                               │
│                                                                │
│  Depends on:                                                   │
│  - memory: Memory (Mem0)                                      │
│  - agent: Agent (Strands)                                     │
│                                                                │
│  Methods:                                                      │
│  - chat(user_input) → str                                     │
│  - get_all_memories() → List[Dict]                            │
│  - reset_memory() → None                                      │
└───────────────┬───────────────────────────────────────────────┘
                │
                │ Uses
                ↓
┌───────────────────────────────────────────────────────────────┐
│                  Mem0 Memory Interface                         │
│                                                                │
│  memory.add(messages, user_id, metadata)                      │
│  memory.search(query, user_id, limit)                         │
│  memory.get_all(user_id)                                      │
│  memory.delete(memory_id)                                     │
└───────────────┬───────────────────────────────────────────────┘
                │
                │ Configured with
                ↓
┌───────────────────────────────────────────────────────────────┐
│                  Backend Configuration                         │
│                                                                │
│  {                                                             │
│    "vector_store": {                                           │
│      "provider": "qdrant",                                     │
│      "config": {...}                                           │
│    },                                                          │
│    "embedder": {                                               │
│      "provider": "huggingface",                                │
│      "config": {...}                                           │
│    },                                                          │
│    "llm": {                                                    │
│      "provider": "litellm",                                    │
│      "config": {...}                                           │
│    }                                                           │
│  }                                                             │
└───────────────────────────────────────────────────────────────┘
```

### Abstraction Layer for Multiple Backends

To support multiple backends, introduce an abstraction:

```
┌───────────────────────────────────────────────────────────────┐
│                      Agent Class                               │
│                                                                │
│  Depends on:                                                   │
│  - memory_manager: MemoryManager (Abstract)                   │
│  - agent: Agent (Strands)                                     │
└───────────────┬───────────────────────────────────────────────┘
                │
                │ Uses
                ↓
┌───────────────────────────────────────────────────────────────┐
│              Abstract MemoryManager Protocol                   │
│                                                                │
│  class MemoryManager(Protocol):                               │
│      def add(self, messages, user_id, metadata) -> None       │
│      def search(self, query, user_id, limit) -> List[Dict]    │
│      def get_all(self, user_id) -> List[Dict]                 │
│      def delete(self, memory_id) -> None                       │
└───────────────┬───────────────────────────────────────────────┘
                │
                │ Implementations
                ↓
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  Mem0Manager    │  │  LangMemManager  │  │  BedrockManager│ │
│  │                 │  │                  │  │                │ │
│  │  Uses:          │  │  Uses:           │  │  Uses:         │ │
│  │  - Mem0         │  │  - langmem       │  │  - AWS Bedrock │ │
│  │  - Qdrant       │  │  - PostgreSQL    │  │  - Managed svc │ │
│  │  - HuggingFace  │  │  - Custom embed  │  │  - Titan embed │ │
│  └─────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Implementation Example

```python
from typing import Protocol, List, Dict, Any, Optional


class MemoryManager(Protocol):
    """Abstract interface for memory backends."""

    def add(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store messages in memory."""
        ...

    def search(
        self,
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for relevant memories."""
        ...

    def get_all(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Retrieve all memories for user."""
        ...

    def delete(
        self,
        memory_id: str
    ) -> None:
        """Delete specific memory."""
        ...


class Mem0Manager:
    """Mem0 implementation of MemoryManager."""

    def __init__(self, config: Dict[str, Any]):
        from mem0 import Memory
        self.memory = Memory.from_config(config)

    def add(self, messages, user_id, metadata=None):
        self.memory.add(
            messages=messages,
            user_id=user_id,
            metadata=metadata or {}
        )

    def search(self, query, user_id, limit=5):
        return self.memory.search(
            query=query,
            user_id=user_id,
            limit=limit
        )

    def get_all(self, user_id):
        return self.memory.get_all(user_id=user_id)

    def delete(self, memory_id):
        self.memory.delete(memory_id=memory_id)


class BedrockMemoryManager:
    """AWS Bedrock implementation of MemoryManager."""

    def __init__(self, config: Dict[str, Any]):
        import boto3
        self.bedrock = boto3.client('bedrock-agent-runtime')
        self.memory_id = config['memory_id']
        self.session_id = config['session_id']

    def add(self, messages, user_id, metadata=None):
        # Convert to Bedrock format and store
        for msg in messages:
            self.bedrock.put_memory(
                memoryId=self.memory_id,
                sessionId=f"{self.session_id}_{user_id}",
                memoryContent=msg['content'],
                memoryMetadata=metadata
            )

    def search(self, query, user_id, limit=5):
        # Query Bedrock memory
        response = self.bedrock.query_memory(
            memoryId=self.memory_id,
            sessionId=f"{self.session_id}_{user_id}",
            query=query,
            maxResults=limit
        )
        return response['memories']

    def get_all(self, user_id):
        # List all memories for session
        response = self.bedrock.list_memories(
            memoryId=self.memory_id,
            sessionId=f"{self.session_id}_{user_id}"
        )
        return response['memories']

    def delete(self, memory_id):
        self.bedrock.delete_memory(memoryId=memory_id)


# Agent uses the abstraction:
class Agent:
    def __init__(
        self,
        memory_manager: MemoryManager,  # Accept any implementation
        user_id: str,
        model: str
    ):
        self.memory_manager = memory_manager
        self.user_id = user_id
        # ... rest of initialization


# Usage - swap backends easily:

# Use Mem0:
mem0_config = {...}
memory_manager = Mem0Manager(mem0_config)
agent = Agent(memory_manager, user_id="alice", model="groq/...")

# Use Bedrock:
bedrock_config = {...}
memory_manager = BedrockMemoryManager(bedrock_config)
agent = Agent(memory_manager, user_id="alice", model="groq/...")
```

**Benefits of abstraction:**
1. Swap backends without changing agent code
2. Test with mock implementations
3. Support multiple backends in same application
4. Migrate between solutions as needs change

---

## Implicit vs Explicit Memory

### Implicit Memory (Automatic)

**Definition**: Agent automatically stores all conversations without being asked.

**When it happens**:
- Every user message is stored immediately
- Every assistant response is stored after generation
- Happens in the background, transparent to user

**Implementation**:
```python
def chat(self, user_input: str) -> str:
    # IMPLICIT: Store user input automatically
    self._store_conversation_async(user_input, None)

    # Process through agent
    response = self.agent(user_input)

    # IMPLICIT: Store response automatically
    self._store_conversation_async(user_input, response)

    return response


def _store_conversation_async(
    self,
    user_message: str,
    assistant_message: str
) -> None:
    """Background storage - user doesn't see this."""
    try:
        messages = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ]

        self.memory.add(
            messages=messages,
            user_id=self.user_id
        )

        logger.debug("Stored conversation in memory")

    except Exception as e:
        logger.error(f"Error storing conversation: {e}")
```

**Flow diagram**:
```
User: "My favorite color is blue"
     │
     ↓ [Automatic storage]
  Memory: Store "My favorite color is blue"
     │
     ↓ [Agent processing]
  Agent: "I'll remember that!"
     │
     ↓ [Automatic storage]
  Memory: Store "I'll remember that!"
     │
     ↓
User receives response

Later:
User: "What's my favorite color?"
     │
     ↓ [Automatic storage]
  Memory: Store "What's my favorite color?"
     │
     ↓ [Agent decides to search]
  Agent: Uses search_memory tool
     │
     ↓ [Finds previous conversation]
  Memory: Returns "My favorite color is blue" (similarity: 0.92)
     │
     ↓ [Agent uses result]
  Agent: "Your favorite color is blue!"
```

---

### Explicit Memory (User-Requested)

**Definition**: User explicitly asks agent to remember something, or agent identifies critical information.

**When it happens**:
- User says: "Remember this", "Don't forget", "Keep in mind"
- Agent identifies important facts: preferences, decisions, commitments
- Information needs special emphasis or categorization

**Implementation**:
```python
@tool
def insert_memory(
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """Explicitly store important information in long-term memory.

    Use this for facts, preferences, or key information that should
    be remembered across conversations. The agent already stores
    conversations automatically, so use this for emphasizing
    particularly important information.
    """
    try:
        logger.info(f"Inserting explicit memory: '{content[:100]}...'")

        memory.add(
            messages=[{"role": "user", "content": content}],
            user_id=user_id,
            metadata=metadata or {}
        )

        response = {
            "status": "success",
            "message": "Memory stored successfully",
            "content": content,
            "metadata": metadata
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        logger.error(f"Error inserting memory: {e}")
        error_response = {
            "status": "error",
            "message": str(e)
        }
        return json.dumps(error_response, indent=2)
```

**Flow diagram**:
```
User: "Please remember that I'm allergic to peanuts"
     │
     ↓ [Automatic storage]
  Memory: Store full message
     │
     ↓ [Agent processing]
  Agent: Recognizes explicit request to remember
     │
     ↓ [Tool decision]
  Agent: Calls insert_memory tool
     │
     ↓ [EXPLICIT storage with emphasis]
  Memory: Store "User allergic to peanuts"
          Metadata: {"type": "health", "importance": "critical"}
     │
     ↓ [Agent responds]
  Agent: "I've made a note that you're allergic to peanuts"
     │
     ↓ [Automatic storage of response]
  Memory: Store agent response
     │
     ↓
User receives confirmation

Later:
User: "Can I eat this cookie?"
     │
     ↓ [Agent searches for dietary restrictions]
  Agent: Uses search_memory with query="dietary allergies"
     │
     ↓ [Finds explicit memory]
  Memory: Returns "User allergic to peanuts" (marked as critical)
     │
     ↓
  Agent: "Check the ingredients for peanuts first, since you're allergic!"
```

---

### Comparison Table

| Aspect | Implicit Memory | Explicit Memory |
|--------|----------------|-----------------|
| **Trigger** | Every conversation turn | User request or agent decision |
| **Visibility** | Background, transparent | Confirmed to user |
| **Purpose** | Complete conversation history | Emphasized important facts |
| **Metadata** | Minimal (timestamp, user_id) | Rich (type, category, importance) |
| **Storage** | Automatic in chat flow | Via insert_memory tool |
| **Retrieval** | Semantic search | Semantic search + metadata filters |
| **Example** | "My name is Alice" stored automatically | "Remember I'm allergic to peanuts" stored with emphasis |

---

### When to Use Each

**Use Implicit (Automatic) Memory**:
- Default for all conversations
- Provides foundation for semantic search
- No overhead for user or agent
- Enables "surprise" recall of forgotten details

**Use Explicit Memory**:
- User explicitly requests: "Remember this"
- Critical information: allergies, constraints, commitments
- Need for categorization: preferences vs facts vs decisions
- When automatic storage isn't sufficient emphasis

**Anti-patterns**:
- Don't use explicit memory for every message (defeats the purpose)
- Don't skip implicit memory thinking explicit is better (you lose history)
- Don't use explicit without clear categorization (adds noise)

---

## Data Flow Diagrams

### Complete User Input Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER TYPES MESSAGE                          │
│                 "What's my favorite color?"                      │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: AGENT.CHAT() RECEIVES INPUT                            │
│                                                                  │
│  def chat(self, user_input: str) -> str:                        │
│      # Validation                                                │
│      if not user_input.strip():                                  │
│          raise ValueError("Empty input")                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: IMPLICIT STORAGE (Background)                          │
│                                                                  │
│  Text: "What's my favorite color?"                              │
│     ↓                                                            │
│  Embedding Model (HuggingFace MiniLM)                           │
│     ↓                                                            │
│  Vector: [0.23, -0.45, 0.67, ..., 0.12]  (384 dimensions)      │
│     ↓                                                            │
│  Qdrant Storage:                                                 │
│    - Collection: agent_memories                                  │
│    - Point ID: generated UUID                                    │
│    - Vector: [0.23, -0.45, ...]                                 │
│    - Payload: {                                                  │
│        "content": "What's my favorite color?",                   │
│        "role": "user",                                           │
│        "user_id": "default_user",                                │
│        "timestamp": "2026-03-15T10:30:00Z"                       │
│      }                                                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: AGENT PROCESSING (Strands SDK)                         │
│                                                                  │
│  agent = Agent(                                                  │
│      model=LiteLLMModel("groq/llama-3.3-70b"),                  │
│      system_prompt="You have memory tools...",                   │
│      tools=[search_memory, insert_memory]                        │
│  )                                                               │
│                                                                  │
│  result = agent(user_input)  # Invokes agent                    │
│                                                                  │
│  Agent analyzes input:                                           │
│  - "What's my favorite color?" is a question about past info    │
│  - System prompt says: use search_memory for past info          │
│  - Decision: CALL search_memory TOOL                            │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: TOOL EXECUTION - search_memory                         │
│                                                                  │
│  Tool call:                                                      │
│    search_memory(                                                │
│        query="user's favorite color",                            │
│        limit=5                                                   │
│    )                                                             │
│                                                                  │
│  Tool implementation:                                            │
│    1. Convert query to embedding                                 │
│       "user's favorite color" → [0.45, -0.23, ...]             │
│                                                                  │
│    2. Query Qdrant for similar vectors                          │
│       memory.search(                                             │
│           query="user's favorite color",                         │
│           user_id="default_user",                                │
│           limit=5                                                │
│       )                                                          │
│                                                                  │
│    3. Qdrant performs vector similarity search:                 │
│       - Compute cosine similarity between query vector           │
│         and all stored vectors                                   │
│       - Rank by similarity score                                 │
│       - Return top 5 matches                                     │
│                                                                  │
│    4. Results:                                                   │
│       [                                                          │
│         {                                                        │
│           "memory": "My favorite color is blue",                 │
│           "score": 0.92,                                         │
│           "id": "mem_abc123",                                    │
│           "created_at": "2026-03-15T10:25:00Z"                   │
│         },                                                       │
│         {                                                        │
│           "memory": "I like blue things",                        │
│           "score": 0.67,                                         │
│           "id": "mem_def456",                                    │
│           "created_at": "2026-03-15T10:26:00Z"                   │
│         }                                                        │
│       ]                                                          │
│                                                                  │
│    5. Format as JSON string and return to agent                 │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: AGENT FORMULATES RESPONSE                              │
│                                                                  │
│  Agent receives tool results:                                    │
│  {                                                               │
│    "status": "success",                                          │
│    "memories": [                                                 │
│      {"memory": "My favorite color is blue", "score": 0.92}     │
│    ]                                                             │
│  }                                                               │
│                                                                  │
│  Agent generates response using LLM:                             │
│  - Input: Original question + tool results + system prompt       │
│  - LLM: Groq llama-3.3-70b via LiteLLM                          │
│  - Output: "Your favorite color is blue!"                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: IMPLICIT STORAGE OF RESPONSE                           │
│                                                                  │
│  Text: "Your favorite color is blue!"                           │
│     ↓                                                            │
│  Embedding Model                                                 │
│     ↓                                                            │
│  Vector: [0.34, -0.56, 0.78, ...]                               │
│     ↓                                                            │
│  Qdrant Storage:                                                 │
│    - Collection: agent_memories                                  │
│    - Point ID: generated UUID                                    │
│    - Payload: {                                                  │
│        "content": "Your favorite color is blue!",                │
│        "role": "assistant",                                      │
│        "user_id": "default_user",                                │
│        "timestamp": "2026-03-15T10:30:05Z"                       │
│      }                                                           │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: RETURN TO USER                                         │
│                                                                  │
│  Display: "Your favorite color is blue!"                        │
└─────────────────────────────────────────────────────────────────┘
```

---

### Memory Retrieval Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    RETRIEVAL TRIGGER                              │
│                                                                   │
│  User asks question requiring past context                       │
│  Agent decides to search memory                                  │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 1: TOOL CALL                                               │
│                                                                   │
│  search_memory(                                                   │
│      query="What project am I working on?",                      │
│      limit=5                                                      │
│  )                                                                │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2: QUERY EMBEDDING                                         │
│                                                                   │
│  HuggingFace Embedder:                                            │
│    Input: "What project am I working on?"                        │
│    Model: all-MiniLM-L6-v2                                       │
│    Output: [0.12, -0.34, 0.56, ..., 0.23]  (384-dim vector)     │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3: QDRANT VECTOR SEARCH                                    │
│                                                                   │
│  Query Qdrant:                                                    │
│    collection: "agent_memories"                                   │
│    vector: [0.12, -0.34, 0.56, ...]                             │
│    filter: {"user_id": "default_user"}                           │
│    limit: 5                                                       │
│                                                                   │
│  Qdrant process:                                                  │
│    1. Load all vectors for user from disk                        │
│    2. Compute cosine similarity with query vector:               │
│       similarity = dot(query_vec, stored_vec) /                  │
│                    (norm(query_vec) * norm(stored_vec))          │
│    3. Rank by similarity score (higher = more similar)           │
│    4. Return top 5 results                                       │
│                                                                   │
│  Results from Qdrant:                                             │
│    [                                                              │
│      {                                                            │
│        "id": "point_123",                                         │
│        "score": 0.91,                                             │
│        "payload": {                                               │
│          "content": "I'm building ML model with scikit-learn",   │
│          "role": "user",                                          │
│          "timestamp": "2026-03-15T09:00:00Z"                      │
│        }                                                          │
│      },                                                           │
│      {                                                            │
│        "id": "point_456",                                         │
│        "score": 0.85,                                             │
│        "payload": {                                               │
│          "content": "Working on customer churn prediction",      │
│          "role": "user",                                          │
│          "timestamp": "2026-03-15T09:05:00Z"                      │
│        }                                                          │
│      }                                                            │
│    ]                                                              │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 4: FORMAT RESULTS                                          │
│                                                                   │
│  Tool formats Qdrant results as JSON:                            │
│  {                                                                │
│    "status": "success",                                           │
│    "count": 2,                                                    │
│    "memories": [                                                  │
│      {                                                            │
│        "id": "mem_123",                                           │
│        "memory": "I'm building ML model with scikit-learn",      │
│        "score": 0.91,                                             │
│        "created_at": "2026-03-15T09:00:00Z"                       │
│      },                                                           │
│      {                                                            │
│        "id": "mem_456",                                           │
│        "memory": "Working on customer churn prediction",         │
│        "score": 0.85,                                             │
│        "created_at": "2026-03-15T09:05:00Z"                       │
│      }                                                            │
│    ]                                                              │
│  }                                                                │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 5: RETURN TO AGENT                                         │
│                                                                   │
│  Agent receives JSON string with memories                        │
│  Agent uses memories to formulate response:                      │
│  "You're working on a machine learning model for customer        │
│   churn prediction using scikit-learn!"                          │
└──────────────────────────────────────────────────────────────────┘
```

---

### Export Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  TRIGGER: Export All Memories                                     │
│                                                                   │
│  agent.get_all_memories()                                         │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 1: QUERY MEM0                                              │
│                                                                   │
│  memory.get_all(user_id="default_user")                          │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 2: QDRANT FULL SCAN                                        │
│                                                                   │
│  Qdrant retrieves all points matching filter:                    │
│    collection: "agent_memories"                                   │
│    filter: {"payload.user_id": "default_user"}                   │
│                                                                   │
│  Returns:                                                         │
│    [                                                              │
│      {                                                            │
│        "id": "point_1",                                           │
│        "vector": [0.12, -0.34, ...],                             │
│        "payload": {                                               │
│          "content": "My name is Alice",                           │
│          "role": "user",                                          │
│          "user_id": "default_user",                               │
│          "timestamp": "2026-03-15T09:00:00Z"                      │
│        }                                                          │
│      },                                                           │
│      {                                                            │
│        "id": "point_2",                                           │
│        "vector": [0.45, -0.67, ...],                             │
│        "payload": {                                               │
│          "content": "I'm a software engineer",                    │
│          "role": "user",                                          │
│          "user_id": "default_user",                               │
│          "timestamp": "2026-03-15T09:01:00Z"                      │
│        }                                                          │
│      },                                                           │
│      ... (all memories for user)                                  │
│    ]                                                              │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 3: MEM0 FORMATS RESULTS                                    │
│                                                                   │
│  Mem0 extracts semantic memories from raw storage:               │
│    [                                                              │
│      {                                                            │
│        "id": "mem_1",                                             │
│        "memory": "User's name is Alice",                          │
│        "created_at": "2026-03-15T09:00:00Z",                      │
│        "updated_at": "2026-03-15T09:00:00Z"                       │
│      },                                                           │
│      {                                                            │
│        "id": "mem_2",                                             │
│        "memory": "User is a software engineer",                   │
│        "created_at": "2026-03-15T09:01:00Z",                      │
│        "updated_at": "2026-03-15T09:01:00Z"                       │
│      }                                                            │
│    ]                                                              │
└────────────────┬─────────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────┐
│  STEP 4: RETURN TO CALLER                                        │
│                                                                   │
│  Function returns list of memory dictionaries                    │
│  Can be:                                                          │
│  - Displayed to user                                              │
│  - Exported to JSON file                                          │
│  - Used for analytics                                             │
│  - Backed up for restore                                          │
└──────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### Initialization Sequence

```
Program Start
     │
     ├─ Load environment variables (.env)
     │  └─ GROQ_API_KEY
     │
     ├─ Initialize Mem0 configuration
     │  ├─ Vector store: Qdrant
     │  │  ├─ Path: ./qdrant_data
     │  │  ├─ Collection: agent_memories
     │  │  └─ Dimensions: 384
     │  ├─ Embedder: HuggingFace
     │  │  └─ Model: all-MiniLM-L6-v2
     │  └─ LLM: LiteLLM/Groq
     │     ├─ Model: llama-3.3-70b-versatile
     │     └─ API Key: from env
     │
     ├─ Create Mem0 Memory instance
     │  └─ memory = Memory.from_config(config)
     │
     ├─ Create tool functions (with closures)
     │  ├─ search_memory = _create_search_memory_tool(memory, user_id)
     │  └─ insert_memory = _create_insert_memory_tool(memory, user_id)
     │
     ├─ Build system prompt
     │  └─ Explains memory capabilities and when to use tools
     │
     ├─ Initialize Strands agent
     │  └─ agent = Agent(
     │        model=LiteLLMModel(model_id),
     │        system_prompt=prompt,
     │        tools=[search_memory, insert_memory]
     │     )
     │
     └─ Ready for chat
```

### Chat Processing Sequence

```
User Input: "My favorite language is Python"
     │
     ├─ agent.chat(user_input)
     │
     ├─ Validate input (not empty)
     │
     ├─ IMPLICIT: Store user message
     │  └─ memory.add([{"role": "user", "content": user_input}], user_id)
     │     └─ Text → Embedding → Qdrant storage
     │
     ├─ Process through Strands agent
     │  └─ result = self.agent(user_input)
     │     │
     │     ├─ Agent analyzes input
     │     │  └─ "Statement of preference, no memory search needed"
     │     │
     │     ├─ Agent may call tools (in this case, none)
     │     │
     │     └─ Agent generates response via LLM
     │        └─ "I'll remember that you prefer Python!"
     │
     ├─ Extract response text from result
     │  └─ Parse content blocks, join text parts
     │
     ├─ IMPLICIT: Store assistant response
     │  └─ memory.add([{"role": "assistant", "content": response}], user_id)
     │     └─ Text → Embedding → Qdrant storage
     │
     └─ Return response to user
```

### Memory Search Sequence

```
User Input: "What's my favorite language?"
     │
     ├─ agent.chat(user_input)
     │
     ├─ IMPLICIT: Store user message
     │
     ├─ Process through agent
     │  └─ Agent analyzes: "Question about past information"
     │     └─ Decision: Call search_memory tool
     │        │
     │        ├─ Tool call: search_memory(query="favorite language", limit=5)
     │        │
     │        ├─ Inside search_memory:
     │        │  ├─ memory.search(query, user_id, limit)
     │        │  │  │
     │        │  │  ├─ Query → Embedding
     │        │  │  │  └─ "favorite language" → [0.45, -0.23, ...]
     │        │  │  │
     │        │  │  ├─ Qdrant vector search
     │        │  │  │  └─ Find similar vectors, rank by score
     │        │  │  │
     │        │  │  └─ Return top results
     │        │  │     └─ [{"memory": "My favorite language is Python", "score": 0.94}]
     │        │  │
     │        │  └─ Format as JSON
     │        │     └─ Return to agent
     │        │
     │        └─ Agent receives tool results
     │
     ├─ Agent formulates response using tool results
     │  └─ "Your favorite language is Python!"
     │
     ├─ IMPLICIT: Store assistant response
     │
     └─ Return to user
```

---

## Comparison with Other Solutions

### Solution Matrix

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        MEMORY SOLUTION COMPARISON                         │
└──────────────────────────────────────────────────────────────────────────┘

                   Mem0          langmem       AWS Bedrock      Manual
                   ────          ───────       ───────────      ──────

Setup             Easy           Medium        Complex          Easy
Complexity        [██░░░]        [████░]       [█████]          [██░░░]

Cost              Free(local)    Free          Paid             Free
                  Paid(cloud)

Infrastructure    None           PostgreSQL    AWS Account      None
Required          (local)        + Redis

Control           High           Full          Low              Full

Abstraction       High           Medium        Very High        None
Level

Production        Good           Good          Excellent        Poor
Ready

Scaling           Good           Excellent     Excellent        Poor

Multi-user        Yes            Yes           Yes              Manual

Semantic          Yes            Yes           Yes              Manual
Search            (built-in)     (built-in)    (built-in)       (requires
                                                                 work)

Customization     Medium         High          Low              Full

Vendor            Moderate       None          High (AWS)       None
Lock-in

Documentation     Good           Good          Excellent        N/A

Community         Growing        Small         Large            N/A

Best For          Dev & Small    Custom        Enterprise       Learning
                  Production     Requirements  with AWS         & Demos
```

### Feature Comparison

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FEATURE SUPPORT                              │
└─────────────────────────────────────────────────────────────────────┘

Feature                    Mem0    langmem    Bedrock    Manual
────────────────────────   ────    ───────    ───────    ──────

Vector Storage              ✓        ✓          ✓         ✗
Semantic Search             ✓        ✓          ✓         ✗
Automatic Extraction        ✓        ✓          ✓         ✗
Multi-user Isolation        ✓        ✓          ✓         △
Metadata Filtering          ✓        ✓          ✓         △
Session Management          ✓        ✓          ✓         ✗
Memory Summarization        ✓        ✓          ✓         ✗
Export/Import               ✓        ✓          △         ✓
Local Storage               ✓        △          ✗         ✓
Cloud Storage               ✓        △          ✓         △
Multiple Backends           ✓        ✓          ✗         △
Custom Embeddings           ✓        ✓          △         ✓
API Access                  ✓        ✓          ✓         ✗
Conversation History        ✓        ✓          ✓         △
Persistent Storage          ✓        ✓          ✓         △

Legend: ✓ = Full Support, △ = Partial/Manual, ✗ = Not Supported
```

### Use Case Recommendations

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WHEN TO USE EACH SOLUTION                         │
└─────────────────────────────────────────────────────────────────────┘

USE MEM0 WHEN:
├─ Building MVP or small production app
├─ Want quick setup with minimal configuration
├─ Need local development with cloud option
├─ Prefer managed solution over self-hosted
├─ Don't have dedicated DevOps resources
└─ Want balance of control and convenience

Examples:
  • SaaS startup building AI chatbot
  • Internal company assistant tool
  • Research prototype with production potential
  • Personal projects with growth plans


USE LANGMEM WHEN:
├─ Need full control over infrastructure
├─ Have specific database requirements
├─ Building custom memory architectures
├─ Want no vendor dependencies
├─ Have DevOps team for maintenance
└─ Need PostgreSQL-based solution

Examples:
  • Enterprise with existing PostgreSQL infrastructure
  • Custom memory patterns not supported elsewhere
  • Data residency requirements
  • Open-source project requiring self-hosting


USE AWS BEDROCK WHEN:
├─ Already invested in AWS ecosystem
├─ Need enterprise-grade reliability
├─ Want fully managed solution
├─ Have compliance requirements met by AWS
├─ Need integration with other AWS services
└─ Budget allows for managed service costs

Examples:
  • Enterprise AWS customers
  • Regulated industries (healthcare, finance)
  • Large-scale production deployments
  • Integration with AWS Step Functions, Lambda, etc.


USE MANUAL IMPLEMENTATION WHEN:
├─ Learning about memory systems
├─ Building proof of concept
├─ Have simple, specific requirements
├─ Want zero external dependencies
├─ Prototyping new memory patterns
└─ Educational purposes

Examples:
  • Classroom exercises and labs
  • Understanding memory fundamentals
  • Rapid prototyping of ideas
  • When existing solutions don't fit at all
```

### Migration Path

```
┌─────────────────────────────────────────────────────────────────────┐
│                      RECOMMENDED MIGRATION PATH                      │
└─────────────────────────────────────────────────────────────────────┘

STAGE 1: LEARNING
   Manual Implementation
   └─ Understand concepts
   └─ Build simple circular buffer
   └─ Learn embedding basics

STAGE 2: PROTOTYPING
   Mem0 (Local)
   └─ Quick setup
   └─ Local Qdrant storage
   └─ Validate features

STAGE 3: SMALL PRODUCTION
   Mem0 (Cloud) OR langmem
   │
   ├─ Choose Mem0 Cloud if:
   │  └─ Want managed solution
   │  └─ Small team
   │  └─ Rapid iteration
   │
   └─ Choose langmem if:
      └─ Have DevOps resources
      └─ Need full control
      └─ Custom requirements

STAGE 4: SCALE
   Mem0 (Cloud) OR AWS Bedrock OR langmem (scaled)
   │
   ├─ Choose Mem0 Cloud if:
   │  └─ Growing steadily
   │  └─ Want simplicity
   │
   ├─ Choose AWS Bedrock if:
   │  └─ AWS-based infrastructure
   │  └─ Need enterprise features
   │  └─ Have AWS expertise
   │
   └─ Choose langmem (scaled) if:
      └─ Custom scaling requirements
      └─ Have infrastructure team
      └─ Want full control
```

---

## Conclusion

This architecture demonstrates a production-ready memory system using:

1. **Clear separation of concerns**: Agent, Memory Manager, Storage Layer
2. **Tool-based abstraction**: Agent uses memory through tools, not direct access
3. **Backend flexibility**: Easy to swap Mem0 for other solutions
4. **Implicit + Explicit**: Automatic storage with selective emphasis
5. **Semantic search**: Vector embeddings for intelligent retrieval
6. **User isolation**: Multi-user support with proper data separation

The system balances simplicity (easy to understand and use) with power (production-ready features), making it suitable for both learning and real applications.

Key takeaways:
- Use production-tested frameworks (Mem0, langmem, Bedrock) over manual solutions
- Start simple (local Mem0), scale as needed (cloud/Bedrock)
- Design with abstraction for flexibility
- Combine implicit and explicit memory for best results
- Semantic search is more powerful than keyword matching
