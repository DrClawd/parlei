# OpenClaw Integration — Parlei Multi-Agent System

> *How Parlei works with OpenClaw's multi-agent framework*

## Overview

Parlei is now integrated with OpenClaw's built-in multi-agent capabilities, providing a dedicated orchestrator agent that manages routing between TUI and Discord channels.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      OpenClaw Framework                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │   TUI Channel│         │Discord Channel│                │
│  │              │         │              │                 │
│  │   User Request│ ───────▶│  Message ────┘                 │
│  └──────┬───────┘         └──────────────┘                 │
│         │                                                   │
│         ▼                                                   │
│  ┌────────────────────────────────────────────┐            │
│  │      Orchestrator Agent                     │            │
│  │    (Claude Sonnet 4.6)                      │            │
│  │                                              │            │
│  │  - Channel routing                           │            │
│  │  - Task assessment                           │            │
│  │  - Multi-agent coordination                  │            │
│  └──────────────┬───────────────────────────────┘            │
│                 │                                             │
│      ┌──────────┼──────────┐                                 │
│      ▼          ▼          ▼                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────────┐                   │
│  │Speak-er │ │Plan-er  │ │Task-er      │                   │
│  └────┬────┘ └────┬────┘ └──────┬──────┘                   │
│       │            │            │                           │
│       └────────────┴────────────┘                           │
│                    │                                        │
│                    ▼                                        │
│         ┌─────────────────────┐                             │
│         │  Specialist Agents  │                             │
│         │  (architecter,      │                             │
│         │   deployer, etc.)   │                             │
│         └─────────────────────┘                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Orchestrator Agent (`shared/orchestrator/orchestrator.md`)

**Role:** Dedicated orchestrator for Parlei within OpenClaw's multi-agent framework. When acting as the user-facing entry point, it inherits Speak-er’s persona so every response feels like Speak-er without needing a separate agent.

**Responsibilities:**
- Route tasks between TUI and Discord
- Assess task complexity and routing
- Coordinate multi-agent delegation
- Manage lateral communication
- Present Speak-er’s tone/personality during channel responses

**Default Model:** Claude Sonnet 4.6

### 2. Routing Configuration (`shared/tools/orchestrator_routing.json`)

Defines:
- Which model to use for the orchestrator
- Routing rules for TUI vs Discord
- Agent enablement and requirements
- Lateral communication grants

### 3. Prompt Templates (`shared/orchestrator/prompts.md`)

Contains prompt templates for:
- Task assessment and routing
- Multi-agent coordination
- Discord/TUI formatting
- Escalation handling

## Configuration

### Orchestrator Model

Configure the orchestrator model in `shared/tools/orchestrator_routing.json`:

```json
{
  "orchestrator": {
    "model": "anthropic/claude-sonnet-4.6"
  }
}
```

### Routing Rules

Modify routing logic in `shared/tools/orchestrator_routing.json`:

```json
{
  "routing": {
    "tui": {
      "primaryAgent": "orchestrator"
    },
    "discord": {
      "primaryAgent": "orchestrator"
    }
  }
}
```

### Agent Enablement

Enable/disable Parlei agents:

```json
{
  "agents": {
    "parlei_speak_er": {
      "enabled": true,
      "required": true
    }
  }
}
```

## Usage

### Starting the System

1. **Clone the forked repository:**
   ```bash
   git clone https://github.com/DrClawd/parlei.git
   cd parlei
   ```

2. **Run OpenClaw bootstrap:**
   ```bash
   scripts/setup.sh openclaw
   ```

3. **Configure OpenClaw multi-agent:**
   Add orchestrator configuration to OpenClaw config or use environment variables.

4. **Initialize Parlei in OpenClaw:**
   ```bash
   openclaw agent spawn --runtime subagent --agentId orchestrator
   ```

### Task Routing

**Simple Request (TUI):**
```
You: "Summarize my meeting notes"

Orchestrator routes → Speak-er → Returns summary
```

**Complex Request (Discord):**
```
You: "Plan a weekend hiking trip and create a packing list"

Orchestrator routes → Speak-er → Plan-er → Task-er → Returns comprehensive plan
```

### Lateral Communication

When Speak-er requests lateral access to Plan-er or Task-er:

```
Orchestrator:
→ Issues grant to Plan-er
→ Coordinates planning workflow
→ Reports completion
→ Returns result to channel
```

## Channel-Specific Considerations

### Discord

**Formatting Rules:**
- Wrap multiple links in `<url>` to suppress embeds
- Use bullet lists instead of markdown tables
- Keep responses concise (max 1-2 paragraphs)
- Add visual cues for action items (•, 1., 2., etc.)

**Thread Management:**
- Respond to thread replies in the same thread
- Use thread replies for follow-ups to maintain conversation context

### TUI

**Formatting Rules:**
- Use clear section headers (##, ###)
- Display results in markdown tables when appropriate
- Keep responses concise but comprehensive
- Use clear section breaks

## Multi-Agent Coordination

### Workflow

1. **Receive Request** → Orchestrator assesses
2. **Route to Speak-er** → Decomposes and evaluates
3. **Plan if Needed** → Plan-er creates PLAN.md
4. **Execute** → Task-er creates TASKS.md
5. **Monitor** → Orchestrator tracks progress
6. **Report** → Consolidated result to channel

### State Tracking

Orchestrator maintains lightweight task registry:

```
Task Registry:
{
  "task_id": "uuid",
  "channel": "tui",
  "status": "in-progress",
  "agents": ["orchestrator", "speak-er", "plan-er"],
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

## Escalation

**Triggers:**
- 3 failed attempts
- Critical errors
- Unresolvable tasks

**Escalation Flow:**
```
Orchestrator → Notifies Human (Spirit of the Forest)
             → Provides full context
             → Offers action options
```

## Troubleshooting

### Orchestrator Not Responding

1. Verify orchestrator agent is spawned:
   ```bash
   sessions_list --kinds subagent
   ```

2. Check routing configuration:
   ```bash
   cat shared/tools/orchestrator_routing.json
   ```

3. Verify OpenClaw multi-agent is enabled

### Task Not Routing Correctly

1. Check channel type detection in logs
2. Verify prompt templates in `shared/orchestrator/prompts.md`
3. Review routing rules in `shared/tools/orchestrator_routing.json`

### Cross-Channel Task Duplication

1. Check task registry for existing tasks
2. Ensure Orchestrator prevents duplicate execution
3. Review lateral communication grants

## Future Enhancements

- [ ] Dashboard for visualizing agent activity
- [ ] Automatic task archival and summary
- [ ] Advanced task prioritization
- [ ] Multi-region / multi-server coordination
- [ ] Real-time agent health monitoring

## Migration from Direct OpenClaw

If you were previously using OpenClaw directly without Parlei:

1. **Backup existing configurations**
2. **Remove direct agent configurations**
3. **Add Orchestrator agent** as primary entry point
4. **Migrate prompts** through Orchestrator routing
5. **Update session configurations** to use Orchestrator

**Key Change:**
```
Before: OpenClaw → Speak-er directly
After:  OpenClaw → Orchestrator → Speak-er
```

This provides centralized routing, cross-channel coordination, and multi-agent orchestration.