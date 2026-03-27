# 🦉 Parlei — OpenClaw Multi-Agent Orchestration

> *A Parliament of Owls working in concert, orchestrated by OpenClaw.*

Parlei is a multi-agent AI orchestration framework that works identically across Claude Code, Augment, Codex, and OpenClaw. This fork integrates Parlei with **OpenClaw's built-in multi-agent framework** using a dedicated orchestrator agent.

## 🎯 What is Parlei?

Parlei (a riff on "parley") is a **multi-agent AI orchestration system** styled after a parliament of owls. It consists of:

- **10 Specialist Agents:** Speak-er, Plan-er, Task-er, Prompt-er, Check-er, Review-er, Architect-er, Deploy-er, Test-er, Re-Origination-er
- **Cross-Environment Support:** Works identically in Claude Code, Augment, Codex, and OpenClaw
- **Shared Memory & Configuration:** Uses symlinks to ensure consistency across environments
- **Nightly Memory Optimization:** Automated deduplication and summarization
- **Backup System:** Automated nightly archives with retention

## ✨ OpenClaw Integration

This fork adds **OpenClaw-specific multi-agent orchestration**:

### New Components

1. **Orchestrator Agent** (`shared/orchestrator/orchestrator.md`)
   - Dedicated Claude Sonnet 4.6 orchestrator
   - Routes tasks between TUI and Discord
   - Manages multi-agent coordination
   - Handles lateral communication

2. **Routing Configuration** (`shared/tools/orchestrator_routing.json`)
   - Defines channel routing rules
   - Agent enablement and requirements
   - Lateral communication grants
   - Model configuration

3. **Prompt Templates** (`shared/orchestrator/prompts.md`)
   - Task assessment templates
   - Discord/TUI formatting rules
   - Multi-agent coordination prompts
   - Escalation handling

4. **Integration Documentation** (`docs/openclaw-integration.md`)
   - Architecture diagrams
   - Configuration guide
   - Usage examples
   - Troubleshooting

### Architecture

```
┌─────────────┐     ┌─────────────┐
│   TUI       │     │  Discord    │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 │
      ┌──────────▼──────────┐
      │  Orchestrator       │
      │  (Claude Sonnet 4.6)│
      └──────────┬──────────┘
                 │
      ┌──────────▼──────────┐
      │    Speak-er         │
      └──────────┬──────────┘
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
    Plan-er  Task-er  ... (specialist agents)
```

## 🚀 Quick Start

### Prerequisites

- OpenClaw installed and running
- Python 3.8+ (for scripts)
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DrClawd/parlei.git
   cd parlei
   ```

2. **Run the OpenClaw bootstrap:**
   ```bash
   scripts/setup.sh openclaw
   ```

3. **Spawn the Orchestrator:**
   ```bash
   sessions_spawn --task "Initialize Parlei Orchestrator" --agentId orchestrator
   ```

4. **Start using Parlei:**

   **In TUI:**
   ```
   You: "Summarize my meeting notes"

   Orchestrator routes → Speak-er → Returns summary
   ```

   **In Discord:**
   ```
   You: "Plan a weekend hiking trip"

   Orchestrator applies Discord formatting → Speak-er → Plan-er → Task-er
   ```

## 🎭 Agent Roster

### Primary Agents
| Agent | Role | Model |
|-------|------|-------|
| **Orchestrator** | OpenClaw routing coordinator | Claude Sonnet 4.6 |
| **Speak-er** | Main interface & orchestrator | Claude Sonnet 4.6 |

### Specialist Agents
| Agent | Role | Uses |
|-------|------|------|
| **Plan-er** | Creates PLAN.md | Strategic planning |
| **Task-er** | Creates TASKS.md | Task breakdown |
| **Prompt-er** | Optimizes prompts | Token efficiency |
| **Check-er** | Plan/Task verification | Completeness check |
| **Review-er** | Code review | Quality & security |
| **Architect-er** | Architecture decisions | Infrastructure |
| **Deploy-er** | DevOps & deployment | CI/CD, infrastructure |
| **Test-er** | Test generation | Unit, integration, E2E |
| **Re-Origination-er** | Project reorganization | Major version restructure |

## 📂 Project Structure

```
parlei/
├── CLAUDE.md                 # Claude Code bootstrap
├── BOOTSTRAP.md              # Base bootstrap (archived)
├── README.md                 # This file
├── README-OPENCLAW.md        # OpenClaw integration guide
├── bootstraps/
│   ├── AUGGIE.md            # Augment-specific bootstrap
│   ├── CODEX.md             # Codex-specific bootstrap
│   └── OPENCLAW.md          # OpenClaw bootstrap with Orchestrator
├── docs/
│   ├── ARCHITECTURE.md      # Infrastructure docs
│   ├── DESIGN.md            # System design
│   ├── PLAN.md              # High-level plan
│   ├── TASKS.md             # Task list
│   ├── openclaw-integration.md # Integration guide
│   ├── install-claude.md    # Claude Code install
│   ├── install-augment.md   # Augment install
│   ├── install-codex.md     # Codex install
│   └── install-openclaw.md  # OpenClaw install
├── shared/
│   ├── agents/              # Agent definitions (.md)
│   ├── orchestrator/        # Orchestrator-specific files
│   │   ├── orchestrator.md  # Orchestrator agent definition
│   │   └── prompts.md       # Prompt templates
│   ├── memory/              # Agent memory files
│   ├── personalities/       # Personality files
│   ├── prompts/             # Reusable prompts
│   └── tools/               # Shared tooling
│       ├── orchestrator_routing.json  # Routing config
│       ├── protocol.md          # Communication protocol
│       └── current_task_spec.md # Task file format
├── backups/                 # Nightly archives
└── scripts/
    ├── setup.sh             # Bootstrap script
    ├── memory_optimize.sh   # Memory optimization
    ├── backup.sh            # Backup script
    └── run_tests.sh         # Test runner
```

## 🔧 Configuration

### Orchestrator Model

Edit `shared/tools/orchestrator_routing.json`:

```json
{
  "orchestrator": {
    "model": "anthropic/claude-sonnet-4.6"
  }
}
```

### Channel Routing

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

## 🎬 Usage Examples

### Example 1: Simple Task (TUI)
```
You: "Summarize my meeting notes"

Orchestrator analyzes:
  - Channel: TUI
  - Type: simple_request
  - Action: Route directly to Speak-er

Orchestrator → Speak-er → "Here's your summary: ..."
```

### Example 2: Complex Task (Discord)
```
You: "Plan a weekend hiking trip and create a packing list"

Orchestrator analyzes:
  - Channel: Discord
  - Type: complex_request
  - Action: Multi-agent delegation

Orchestrator → Speak-er → Plan-er → Task-er

Results:
  - SPEAK_ER: "Task decomposed into planning and execution"
  - PLAN_ER: "Here's your plan (PLAN.md created)"
  - TASK_ER: "Here are the tasks (TASKS.md created)"
  - Orchestrator → You: "Complete hiking trip plan and packing list"
```

### Example 3: Lateral Communication
```
Speak-er: "I need to create a complex plan for this task"

Orchestrator:
  - Verifies request
  - Issues grant to Plan-er
  - Coordinates planning workflow

Plan-er → Speak-er → Orchestrator → You
```

## 📡 Communication Protocol

### Request Format
```json
{
  "from": "orchestrator",
  "to": "speak-er",
  "request_id": "req-orchestrator-20260327-001",
  "items": [...]
}
```

### Response Format
```json
{
  "from": "speak-er",
  "to": "orchestrator",
  "request_id": "req-orchestrator-20260327-001",
  "items": [...]
}
```

## 🛠️ Tools & Scripts

### Setup Script
```bash
scripts/setup.sh openclaw
```

Creates symlinks, registers cron jobs for nightly memory optimization and backup.

### Memory Optimization
```bash
scripts/memory_optimize.sh
```

Deduplicates episodic logs, promotes frequent items to long_term.md, prunes stale entries, runs LLM summarization.

### Backup
```bash
scripts/backup.sh
```

Creates date-based archive of `shared/`, with retention pruning.

### Tests
```bash
scripts/run_tests.sh
```

Runs all unit, integration, and functionality tests.

## 🔍 Troubleshooting

### Orchestrator Not Responding
```bash
# Check orchestrator status
sessions_list --kinds subagent

# Check routing config
cat shared/tools/orchestrator_routing.json
```

### Task Not Routing Correctly
1. Check channel type detection in logs
2. Verify prompt templates in `shared/orchestrator/prompts.md`
3. Review routing rules in `shared/tools/orchestrator_routing.json`

### Cross-Channel Task Duplication
1. Check task registry for existing tasks
2. Ensure Orchestrator prevents duplicate execution
3. Review lateral communication grants

## 📚 Documentation

- **System Design:** `docs/DESIGN.md` — Complete architecture and design principles
- **Integration Guide:** `docs/openclaw-integration.md` — OpenClaw-specific integration
- **Installation Guides:** `docs/install-*.md` — Environment-specific installation
- **Task List:** `docs/TASKS.md` — Complete task breakdown

## 🎯 Features

- ✅ **Multi-Environment Support:** Claude, Augment, Codex, OpenClaw
- ✅ **Multi-Agent Orchestration:** 10 specialized agents
- ✅ **Channel Routing:** TUI and Discord coordination
- ✅ **Shared Memory:** Persistent, per-agent memory
- ✅ **Nightly Optimization:** Automated deduplication and summarization
- ✅ **Backup System:** Automated archives with retention
- ✅ **Resilient Agents:** Interrupt recovery via `current_task.md`
- ✅ **Escalation:** Human intervention when needed
- ✅ **Token Optimization:** Prompt templates and caching
- ✅ **Open Source First:** All tools and runtimes are OSS

## 🔮 Roadmap

- [ ] Dashboard for visualizing agent activity
- [ ] Automatic task archival and summaries
- [ ] Advanced task prioritization
- [ ] Multi-region / multi-server coordination
- [ ] Real-time agent health monitoring
- [ ] Web UI (SvelteKit-based)

## 📝 License

This project follows open-source principles. See repository for specific license terms.

## 🤝 Contributing

Contributions welcome! Please read `docs/DESIGN.md` for architecture guidelines.

## 📮 Support

For issues and questions:
1. Check `docs/openclaw-integration.md` for integration help
2. Review `docs/TASKS.md` for complete task list
3. Consult `docs/ARCHITECTURE.md` for architecture questions

---

**Parlei:** A Parliament of Owls, working in concert under the guidance of the Spirit of the Forest. 🦉