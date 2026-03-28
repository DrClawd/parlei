# 🎯 Per-Agent Model Configuration

**Feature:** Each Parlei agent can optionally use a different LLM provider and model.

---

## How It Works

1. **Configuration File:** `shared/tools/orchestrator_routing.json` defines `model` for each agent
2. **Orchestrator Resolution:** Reads the config and spawns agents with their specified models
3. **Default Fallback:** If no model specified, uses "default" (OpenClaw's configured model)

---

## Configuration Format

```json
{
  "agents": {
    "parlei_speak_er": {
      "enabled": true,
      "required": true,
      "model": "anthropic/claude-sonnet-4-6"  // Example: Fixed model
    },
    "parlei_plan_er": {
      "enabled": true,
      "required": false,
      "model": "default"  // Uses system default
    },
    "parlei_task_er": {
      "enabled": true,
      "required": false,
      "model": "ollama/kimi-k2.5:cloud"  // Example: Different provider
    }
  }
}
```

---

## Supported Model Specifications

| Format | Example | Resolution |
|--------|---------|------------|
| Full Provider + Model | `"anthropic/claude-sonnet-4-6"` | Exact model from provider |
| Provider-Only | `"anthropic"` | Uses default model for that provider |
| Local Model | `"ollama/kimi-k2.5:cloud"` | Uses local model server |
| Default | `"default"` | Uses OpenClaw's configured default |
| Model-Only | `"gpt-4"` | Provider-based lookup |

---

## Dynamic Model Selection Strategy

The orchestrator now supports:

1. **Static Models:** Per-agent fixed models
2. **Dynamic Models:** Channel-specific or task-specific overrides
3. **Provider Fallback:** Use default from configured provider if specific model unavailable
4. **Rate Limit Awareness:** Prefers faster models for simple tasks, powerful models for complex tasks

---

## Usage Example

**In `orchestrator_routing.json`:**
```json
{
  "agents": {
    "parlei_speak_er": {
      "model": "anthropic/claude-3.5-sonnet"
    },
    "parlei_plan_er": {
      "model": "openai/gpt-4"
    },
    "parlei_task_er": {
      "model": "ollama/kimi-k2.5:cloud"
    }
  }
}
```

**In `shared/orchestrator/orchestrator.md`:**
```
Now reads config and spawns agents with their specified models:
- Speak-er uses claude-3.5-sonnet for fast responses
- Plan-er uses gpt-4 for complex reasoning
- Task-er uses kimi-k2.5 for execution
```

---

## Benefits

- **Cost Optimization:** Use cheaper models for simple tasks, expensive ones only when needed
- **Speed:** Deploy fast models for TUI, powerful ones for Discord
- **Quality:** Tailor model selection to task complexity
- **Flexibility:** Mix providers (Anthropic, OpenAI, Ollama, etc.)

---

**Last Updated:** 2026-03-28