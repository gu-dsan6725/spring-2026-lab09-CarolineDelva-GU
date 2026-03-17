# Lab Exercise: Agent Observability with Braintrust

This lab has two problems. Problem 1 is required (50 points). Problem 2 is optional for additional credit (50 points).

---

## Problem 1: Running and Analyzing Agent Observability (50 Points)

### Objective
Run the agent, observe its behavior, and analyze the observability data in Braintrust.

### Instructions

#### Step 1: Run the Agent (10 points)

1. Ensure your `.env` file is configured with:
   - `ANTHROPIC_API_KEY`
   - `BRAINTRUST_API_KEY`
   - `BRAINTRUST_PROJECT` (using format `project_name:your-project-name`)

2. Run the agent:
   ```bash
   cd simple-agent-observability
   uv run python agent.py
   ```

3. Ask the agent **at least 3 different questions** that will trigger the DuckDuckGo search tool. Examples:
   - "What is the latest news about artificial intelligence?"
   - "Who won the 2024 Nobel Prize in Physics?"
   - "What are the current trends in machine learning?"

4. Let the agent complete all responses before exiting (type `quit`)

#### Step 2: Explore Braintrust Dashboard (15 points)

1. Go to [https://www.braintrust.dev/](https://www.braintrust.dev/)
2. Navigate to your project
3. Explore the **Logs** tab
4. Click on individual traces to see detailed information
5. Explore different tabs and views available in Braintrust

Take **at least 3 screenshots** showing:
- Overview of multiple traces (Logs view)
- Detailed view of a single trace showing spans
- Metrics view showing token usage, latency, or other metrics

Save these screenshots with clear filenames:
- `braintrust-overview.png`
- `braintrust-trace-details.png`
- `braintrust-metrics.png`

#### Step 3: Write Analysis Document (25 points)

Create a file named `analysis.md` in the `simple-agent-observability` folder.

**⚠️ IMPORTANT NOTICE:**
This analysis document **MUST BE WRITTEN BY YOU**, not AI-generated. This is the only way to truly discover and learn from the observability data. We can detect AI-generated content, and using AI for this analysis will result in **zero points** for Problem 1.

**What We're Looking For:**

Write **2-3 short paragraphs** describing your observations from the Braintrust dashboard, along with your screenshots. Your analysis should cover:

- What you see in the traces (hierarchy of operations, spans, tool calls)
- What metrics are captured and what patterns you notice
- Any interesting observations about performance, token usage, or behavior differences across your queries

Include your screenshots with brief captions explaining what they show.

This is an open-ended reflection on what you discover in the observability data - there's no single "right" answer. We want to see that you explored the dashboard and understood what the traces and metrics are telling you.

### Submission for Problem 1
Submit:
- `analysis.md` (your written analysis)
- Screenshots (at least 3)

---

## Problem 2: Adding MCP Server Integration (Optional - 50 Points)

### Objective
Extend the agent to use an MCP (Model Context Protocol) server for additional capabilities, demonstrating how to integrate external tools and observe them in Braintrust.

### Instructions

#### Step 1: Choose an MCP Server (5 points)

You can use one of these public MCP servers:

1. **Context7** (Recommended): Documentation search
   - URL: `https://mcp.context7.com/mcp`
   - Provides: Search across programming documentation

2. **Other Public MCP Servers**:
   - You can explore other MCP servers from the MCP directory
   - Document which one you chose and why

#### Step 2: Add MCP Tools Using Strands (25 points)

Strands has built-in support for MCP servers through the `MCPClient` class.

**Approach**: Use the streamable HTTP MCP protocol to connect to Context7 or another public MCP server, list available tools, and add them to your agent.

**Steps to Implement**:

1. **Import required modules**:
   ```python
   from strands.tools.mcp import MCPClient
   from mcp.client.streamable_http import streamablehttp_client
   ```

2. **Create a transport callable for the MCP server**:
   ```python
   def create_streamable_http_transport():
       return streamablehttp_client("https://mcp.context7.com/mcp")
   ```

3. **Initialize MCPClient and get tools**:
   ```python
   streamable_http_mcp_client = MCPClient(create_streamable_http_transport)

   # Use context manager to list and get tools
   with streamable_http_mcp_client:
       mcp_tools = streamable_http_mcp_client.list_tools_sync()
   ```

4. **Add MCP tools to your agent**:
   ```python
   agent = Agent(
       system_prompt=system_prompt,
       model=model,
       tools=[duckduckgo_search] + mcp_tools  # Combine DuckDuckGo and MCP tools
   )
   ```

**How it Works**:
- The `MCPClient` connects to the MCP server using streamable HTTP transport
- The `list_tools_sync()` method retrieves all available tools from the server
- These tools are then added to the agent's tool list
- The agent can use both DuckDuckGo and MCP tools seamlessly

**Alternative MCP Servers**:
If you want to use a different MCP server, you can find more at the [MCP directory](https://github.com/modelcontextprotocol/servers).

**Hints:**
- Use the context manager (`with` statement) to ensure proper connection handling
- The MCP tools will appear alongside your other tools in Braintrust traces
- Check the Braintrust dashboard to see how MCP tool calls differ from regular tool calls

#### Step 4: Test with MCP Integration (10 points)

Run the modified agent and test the MCP integration:

Ask the agent to:
1. Connect to the Context7 MCP server
2. List available tools
3. Load the tools
4. Use one of the loaded tools to answer a question

Example:
- "Connect to Context7 MCP server at https://mcp.context7.com/mcp and show me what tools are available"
- "How do I use FastAPI with async endpoints?" (should use loaded MCP tools)

Take a screenshot in Braintrust showing the MCP tool being invoked in a trace.

#### Step 5: Document Your Implementation (5 points)

Create a simple file named `analysis-mcp-observability.md` with:

1. **One screenshot** showing MCP tool call in Braintrust trace
2. **Short explanation** (1-2 paragraphs) describing:
   - Which MCP server you connected to
   - What you observed in the Braintrust traces when MCP tools were called
   - Brief comparison of MCP tool invocations vs DuckDuckGo tool invocations

**Example Structure:**
```markdown
# MCP Observability Analysis

![MCP Tool in Braintrust](braintrust-mcp-tool.png)
*Screenshot showing MCP tool invocation in Braintrust trace*

I connected to the Context7 MCP server and loaded its documentation search tools...

In the Braintrust traces, I observed that...
```

### Submission for Problem 2
Submit:
- Modified `agent.py` with mcp_client tool added
- `analysis-mcp-observability.md` (1 screenshot + short explanation)
- Screenshot file showing MCP tool in Braintrust trace

---

## Grading Rubric

### Problem 1: Agent Observability Analysis (50 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **Agent Execution** | 10 | Successfully ran agent with 3+ questions |
| **Screenshots** | 15 | Clear, well-labeled screenshots of Braintrust (3+) |
| **Written Analysis** | 25 | 2-3 paragraphs with thoughtful observations about traces, metrics, and patterns |

**Penalties:**
- AI-generated analysis: -50 points (zero credit)
- Missing screenshots: -5 points each
- Incomplete analysis: -10 points

### Problem 2: MCP Integration (Optional - 50 points)

| Component | Points | Criteria |
|-----------|--------|----------|
| **MCP Selection** | 5 | Chose and documented MCP server |
| **Implementation** | 25 | Added mcp_client tool to agent.py |
| **Testing** | 10 | Successfully connected, listed, and loaded MCP tools |
| **Documentation** | 10 | analysis-mcp-observability.md with screenshot and explanation |

---

## Resources

- [Braintrust Documentation](https://www.braintrust.dev/docs)
- [OpenTelemetry GenAI Semantics](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Strands Documentation](https://strandsagents.com/)
- [MCP Documentation](https://modelcontextprotocol.io/)
- Context7 MCP Server: `https://mcp.context7.com/mcp`

