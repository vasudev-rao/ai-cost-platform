# AI Cost Intelligence Platform — Python SDK

## Installation

```bash
pip install httpx  # Only dependency
```

## Quick Start

```python
from ai_cost_sdk import AIcostClient
import openai
import anthropic

# Initialize the SDK client
cost_client = AIcostClient(
    api_key="your-project-api-key",
    platform_url="https://api.aicostplatform.com",
    org_id="your-org-id",
    project_id="your-project-id",
    environment="production",
)

# Wrap OpenAI — zero code changes to your existing calls
openai_client = cost_client.wrap_openai(openai.OpenAI(api_key="sk-..."))
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Summarize this document..."}]
)
# ✅ Cost automatically tracked in background thread

# Wrap Anthropic
anthropic_client = cost_client.wrap_anthropic(anthropic.Anthropic(api_key="sk-ant-..."))
response = anthropic_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)
# ✅ Cost automatically tracked

# Context manager — auto-flushes on exit
with AIcostClient(api_key="...", platform_url="...", org_id="...", project_id="...") as client:
    wrapped = client.wrap_openai(openai.OpenAI())
    # ... use wrapped client
```

## Features
- 🔄 Non-blocking background thread — zero latency overhead
- 📦 Automatic batching — configurable batch size and flush interval
- 🛡️ Fault tolerant — exceptions in tracking never affect main flow
- 🔀 Provider-agnostic — OpenAI, Anthropic, Gemini, Bedrock supported
- 🏷️ Tag support — add team, feature, environment tags to every event
