# Architecture: Observability for AI Agents

## Overview

This document explains the observability architecture of our AI agent, focusing on OpenTelemetry (OTEL) and its GenAI semantic conventions.

## What is OpenTelemetry (OTEL)?

**OpenTelemetry** is an open-source observability framework that provides:
- Standardized APIs and SDKs for collecting telemetry data
- Support for traces, metrics, and logs
- Vendor-neutral instrumentation
- Integration with major observability platforms

### Key Benefits

1. **Standardization**: Use the same instrumentation across different backends
2. **Vendor-Neutral**: Switch observability platforms without changing code
3. **Comprehensive**: Traces, metrics, and logs in one framework
4. **Community-Driven**: Backed by CNCF (Cloud Native Computing Foundation)

### Core Concepts

- **Traces**: Track requests through distributed systems
- **Spans**: Individual operations within a trace
- **Metrics**: Numerical measurements over time
- **Attributes**: Key-value pairs providing context

## OpenTelemetry GenAI Semantic Conventions

### What Are Semantic Conventions?

**Semantic conventions** define standard names and meanings for telemetry data. For GenAI, they specify:
- Attribute names for LLM operations
- Metric names for AI workloads
- Span names for agent operations
- Event structures for inputs/outputs

Official Documentation: [https://opentelemetry.io/docs/specs/semconv/gen-ai/](https://opentelemetry.io/docs/specs/semconv/gen-ai/)

### Why GenAI Semantics Matter

1. **Consistency**: All AI tools report the same metrics
2. **Interoperability**: Switch between observability platforms easily
3. **Best Practices**: Follow industry standards
4. **Automation**: Tools can parse and analyze standardized data

## OpenTelemetry GenAI Metrics

The OTEL GenAI specification defines five key metrics for monitoring AI applications:

### Client Metrics

These metrics track the client-side operations when calling LLM APIs:

#### 1. `gen_ai.client.token.usage`
- **Type**: Histogram
- **Unit**: `{token}` (tokens)
- **Measures**: Number of input and output tokens used
- **Status**: Recommended (when token counts are readily available)
- **Use Case**: Track token consumption and costs
- **Attributes**:
  - Operation name
  - Provider name (e.g., "anthropic", "openai")
  - Token type (input/output)

**Why It Matters**: Token usage directly correlates to API costs. This metric helps you:
- Monitor spending in real-time
- Optimize prompts to reduce tokens
- Predict monthly costs
- Identify expensive operations

#### 2. `gen_ai.client.operation.duration`
- **Type**: Histogram
- **Unit**: `s` (seconds)
- **Measures**: GenAI operation duration
- **Status**: Required
- **Use Case**: Track latency and performance
- **Attributes**:
  - Operation name
  - Provider name
  - Error type (if operation fails)

**Why It Matters**: Latency affects user experience. This metric helps you:
- Identify slow operations
- Compare provider performance
- Set SLA thresholds
- Detect performance regressions

### Server Metrics

These metrics track server-side operations when hosting your own AI services:

#### 3. `gen_ai.server.request.duration`
- **Type**: Histogram
- **Unit**: `s` (seconds)
- **Measures**: Server request duration (time-to-last-byte or last output token)
- **Status**: Recommended
- **Use Case**: Monitor server-side performance
- **Attributes**:
  - Provider name
  - Model information
  - Server details

**Why It Matters**: Critical for production deployments. Helps you:
- Monitor server health
- Identify bottlenecks
- Scale infrastructure appropriately
- Meet SLA requirements

#### 4. `gen_ai.server.time_per_output_token`
- **Type**: Histogram
- **Unit**: `s` (seconds)
- **Measures**: Time per output token generated (after the first token)
- **Status**: Recommended
- **Use Case**: Track streaming performance
- **Attributes**:
  - Provider name
  - Model information

**Why It Matters**: For streaming responses, this shows generation speed. Helps you:
- Optimize streaming experience
- Compare model performance
- Detect generation slowdowns
- Improve perceived latency

#### 5. `gen_ai.server.time_to_first_token`
- **Type**: Histogram
- **Unit**: `s` (seconds)
- **Measures**: Time to generate the first token for successful responses
- **Status**: Recommended
- **Use Case**: Track perceived latency
- **Attributes**:
  - Provider name
  - Model information

**Why It Matters**: First token latency is critical for UX. Helps you:
- Improve time-to-first-byte
- Reduce perceived waiting time
- Optimize prompt processing
- Compare model initialization times

### Additional Signals

Beyond metrics, OTEL GenAI conventions also cover:

1. **Events**: Capture GenAI inputs and outputs
2. **Model Spans**: Track individual model operations
3. **Agent Spans**: Monitor agent and framework operations

Full specification: [https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/)

## Architecture of This Agent

### Component Stack

```
┌─────────────────────────────────────┐
│         User Interface              │
│        (CLI / Terminal)             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Strands Agent                │
│  - System prompt                    │
│  - Tool orchestration               │
│  - LLM interaction                  │
└──────────┬────────────┬─────────────┘
           │            │
    ┌──────▼────┐  ┌───▼──────────┐
    │  Tools    │  │  MCP Server  │
    │           │  │              │
    │ DuckDuckGo│  │  Context7    │
    └───────────┘  └──────────────┘
           │
┌──────────▼──────────────────────────┐
│      LiteLLM Layer                  │
│  (Anthropic Claude Haiku)           │
└──────────┬──────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│   OpenTelemetry Layer               │
│  - TracerProvider                   │
│  - Span creation                    │
│  - Attribute collection             │
└──────────┬──────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│  BraintrustSpanProcessor            │
│  - Collect spans                    │
│  - Add context                      │
│  - Export to Braintrust             │
└──────────┬──────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│     Braintrust Platform             │
│  - Trace storage                    │
│  - Visualization                    │
│  - Analytics                        │
└─────────────────────────────────────┘
```

### Data Flow

1. **User Input**: User asks a question
2. **Agent Processing**: Strands agent analyzes the request
3. **Tool Selection**: Agent decides which tools to use
4. **Tool Execution**: DuckDuckGo or Context7 is invoked
5. **LLM Call**: Claude Haiku generates response
6. **Telemetry Collection**: OTEL captures all operations
7. **Span Export**: Braintrust processor sends data
8. **Visualization**: Braintrust displays traces

### What Gets Traced?

Every operation creates a span with attributes:

```python
Agent Span
├── Tool Call Span (DuckDuckGo)
│   ├── query: "latest AI news"
│   ├── results: [...]
│   └── duration: 1.2s
├── LLM Call Span
│   ├── model: "claude-3-5-haiku-20241022"
│   ├── prompt_tokens: 150
│   ├── completion_tokens: 300
│   └── duration: 2.5s
└── Total Duration: 3.8s
```

## Implementation Details

### Initialization

```python
# Create TracerProvider
tracer_provider = TracerProvider()

# Add Braintrust processor
tracer_provider.add_span_processor(BraintrustSpanProcessor())

# Configure Strands telemetry
telemetry = StrandsTelemetry(tracer_provider=tracer_provider)

# Create agent with telemetry
agent = Agent(
    system_prompt=system_prompt,
    model="claude-3-5-haiku-20241022",
    telemetry=telemetry,
    ...
)
```

### Automatic Instrumentation

Strands automatically instruments:
- Agent invocations
- Tool calls
- LLM requests
- MCP server calls
- Error tracking

### Manual Instrumentation

You can add custom spans:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("custom_operation") as span:
    span.set_attribute("custom_attribute", "value")
    # Your code here
```

## Using Alternative Observability Platforms

While this lab uses Braintrust, you can use any OTEL-compatible platform:

### Switching Platforms

Replace `BraintrustSpanProcessor()` with another exporter:

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure OTLP exporter (works with many platforms)
otlp_exporter = OTLPSpanExporter(
    endpoint="https://your-platform.com:4317",
    headers={"api-key": "your-api-key"}
)

# Add to tracer provider
tracer_provider.add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)
```

### Compatible Platforms

- **Langfuse**: OpenTelemetry support
- **Phoenix**: Native OTEL integration
- **Datadog**: APM with OTEL
- **New Relic**: OpenTelemetry protocol
- **Honeycomb**: OTEL-native
- **Jaeger**: OTEL-compatible
- **Grafana Tempo**: OTEL tracing

## Best Practices

### 1. Always Use Semantic Conventions

Follow OTEL GenAI conventions for consistency:
```python
span.set_attribute("gen_ai.system", "anthropic")
span.set_attribute("gen_ai.request.model", "claude-3-5-haiku-20241022")
```

### 2. Add Contextual Attributes

Include business context:
```python
span.set_attribute("user_id", user_id)
span.set_attribute("session_id", session_id)
span.set_attribute("environment", "production")
```

### 3. Track Errors Properly

Set span status on errors:
```python
try:
    result = await agent.invoke_async(query)
except Exception as e:
    span.set_status(StatusCode.ERROR)
    span.record_exception(e)
```

### 4. Sample Appropriately

In production, use sampling:
```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
tracer_provider = TracerProvider(
    sampler=TraceIdRatioBased(0.1)
)
```

### 5. Monitor Costs

Set up alerts for:
- Token usage thresholds
- Latency SLAs
- Error rates
- Cost budgets

## Security Considerations

### PII Protection

Never log sensitive data:
```python
# Bad
span.set_attribute("user_email", email)

# Good
span.set_attribute("user_id_hash", hash(user_id))
```

### API Key Security

- Never log API keys
- Use environment variables
- Rotate keys regularly
- Use key management services

### Data Retention

Configure retention policies:
- Production: 30 days
- Development: 7 days
- Delete on request (GDPR)

## Performance Impact

OpenTelemetry has minimal overhead:
- ~1-5ms per operation
- Asynchronous export
- Configurable sampling
- Efficient serialization

### Optimization Tips

1. Use batch processing
2. Enable sampling in production
3. Set reasonable retention periods
4. Use tail-based sampling for errors

## Conclusion

Observability is essential for production AI agents. OpenTelemetry provides:
- Standardized instrumentation
- Vendor-neutral telemetry
- Comprehensive visibility
- Production-ready tooling

By following OTEL GenAI semantic conventions, you can:
- Monitor agent performance
- Debug issues quickly
- Optimize costs
- Ensure reliability

## Additional Resources

- **OpenTelemetry**: [https://opentelemetry.io/](https://opentelemetry.io/)
- **GenAI Semantics**: [https://opentelemetry.io/docs/specs/semconv/gen-ai/](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- **GenAI Metrics**: [https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/)
- **Braintrust**: [https://www.braintrust.dev/](https://www.braintrust.dev/)
- **Strands**: [https://strandsagents.com/](https://strandsagents.com/)
