# 🦉 Parlei — Multi-Agent Orchestration Framework

> *A Parliament of Owls working in concert, orchestrated by Claude Sonnet.*

Parlei is a **multi-agent AI orchestration system** that works identically across Claude Code, Augment, Codex, and OpenClaw. It consists of 10 specialist agents that collaborate to complete complex tasks.

## ✨ Features

- 🦉 **Multi-Agent System** — 10 specialist agents with clear roles
- 🔄 **Cross-Environment Support** — Works identically in Claude, Augment, Codex, and OpenClaw
- 📝 **Shared Memory** — Persistent, per-agent memory with nightly optimization
- 💾 **Backup System** — Automated nightly archives with retention
- 🤖 **Resilient Agents** — Interrupt recovery via `current_task.md`
- 🎯 **Task Tracking** — PLAN.md + TASKS.md for comprehensive task breakdown
- 🔗 **Lateral Communication** — Agents can request access to specialists
- 📊 **Token Optimization** — Prompt templates and caching for efficiency
- ⚡ **Escalation** — Human intervention when tasks fail

## 🎭 Agent Roster

| Agent | Role | Key Uses |
|-------|------|----------|
| **Orchestrator** | OpenClaw routing coordinator | TUI ↔ Discord coordination |
| **Speak-er** | Main interface & orchestrator | Task assessment, agent coordination |
| **Plan-er** | Creates PLAN.md | Strategic planning, workflow design |
| **Task-er** | Creates TASKS.md | Detailed task breakdown |
| **Prompt-er** | Optimizes prompts | Token efficiency, prompt engineering |
| **Check-er** | Plan/Task verification | Completeness, consistency checks |
| **Review-er** | Code review | Quality, security, style |
| **Architect-er** | Architecture decisions | Infrastructure, system design |
| **Deploy-er** | DevOps & deployment | CI/CD, infrastructure as code |
| **Test-er** | Test generation | Unit, integration, E2E tests |
| **Re-Origination-er** | Project reorganization | Major version restructure |

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ (for scripts)
- Git
- Claude Sonnet 4.6 (or compatible model)
- Optional: OpenClaw for multi-channel support

### Installation

```bash
# Clone the repository
git clone https://github.com/DrClawd/parlei.git
cd parlei

# Run the bootstrap script
scripts/setup.sh openclaw
```

### Usage

**In TUI:**
```
You: "Summarize my meeting notes"

Orchestrator → Speak-er → Returns summary
```

**In Discord:**
```
You: "Plan a weekend hiking trip"

Orchestrator applies Discord formatting → Speak-er → Plan-er → Task-er
```

**Multi-Agent Workflow:**
```
1. Speak-er receives request
2. Speak-er decomposes task
3. Plan-er creates PLAN.md (if needed)
4. Task-er creates TASKS.md
5. Specialists execute tasks
6. Review-er validates results
7. Speak-er returns consolidated result
```

## 📂 Project Structure

```
parlei/
├── CLAUDE.md                 # Claude Code bootstrap
├── BOOTSTRAP.md              # Base bootstrap (archived)
├── README.md                 # This file
├── README-OPENCLAW.md        # OpenClaw integration guide
├── CHANGES.md                # Complete change log
├── bootstraps/
│   ├── AUGGIE.md            # Augment-specific bootstrap
│   ├── CODEX.md             # Codex-specific bootstrap
│   └── OPENCLAW.md          # OpenClaw bootstrap with Orchestrator
├── docs/
│   ├── ARCHITECTURE.md      # Infrastructure docs
│   ├── DESIGN.md            # System design
│   ├── PLAN.md              # High-level plan
│   ├── TASKS.md             # Task list
│   ├── openclaw-integration.md # OpenClaw integration
│   └── install-*.md         # Environment-specific installs
├── shared/
│   ├── agents/              # Agent definitions (.md)
│   ├── orchestrator/        # Orchestrator-specific files
│   ├── memory/              # Agent memory files
│   ├── personalities/       # Personality files
│   ├── prompts/             # Reusable prompts
│   └── tools/               # Shared tooling
├── backups/                 # Nightly archives
└── scripts/
    ├── setup.sh             # Bootstrap script
    ├── memory_optimize.sh   # Memory optimization
    ├── backup.sh            # Backup script
    └── run_tests.sh         # Test runner
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

## 🧠 Memory System

### Daily Memory
- `memory/YYYY-MM-DD.md` — Raw daily logs
- Automatically created for each day

### Long-Term Memory
- `MEMORY.md` — Curated long-term memories
- Updated nightly via optimization script
- Searchable via `scripts/memory_search_enhanced.py`

### Retention Policy
- Keep 90 days of daily memory
- Archive old memory before deletion
- Long-term memory retained indefinitely

## 🔄 Workflow

### Task Decomposition
```
Speak-er receives request
  ↓
Analyze intent and complexity
  ↓
Determine if planning is needed
  ↓
Create PLAN.md (if complex)
  ↓
Create TASKS.md (if needed)
  ↓
Assign to specialists
  ↓
Monitor progress
  ↓
Return consolidated result
```

### Interruption Recovery
```
Agent encounters interruption
  ↓
Create/Update `shared/memory/<agent>/current_task.md`
  ↓
Set Status: in-progress
  ↓
Save progress and checkpoints
  ↓
On resume: Read `current_task.md`
  ↓
Notify human before resuming
```

## 🔗 Lateral Communication

Agents can request access to other agents:

```json
{
  "from": "speak-er",
  "to": "plan-er",
  "request_id": "req-speak-er-20260327-001",
  "items": [
    {
      "id": 1,
      "type": "lateral_access",
      "description": "Speak-er needs to create a complex plan"
    }
  ]
}
```

### Grant Process
1. Orchestrator verifies request
2. Issues grant to target agent
3. Coordinates task execution
4. Reports completion back to requesting agent
5. Returns result to channel

## 💾 Backup System

### Schedule
- Nightly (cron job)
- Automatic

### Contents
- `shared/` directory
- All agent memory
- All configuration files

### Retention
- Keep last 90 days
- Archive older backups
- Prune oldest before adding new

## ⚡ Optimization

### Token Efficiency
- Prompt templates in `shared/prompts/`
- Cached common prompts
- Compressed intermediate results

### Memory Efficiency
- Daily deduplication
- Long-term promotion
- Stale entry pruning
- LLM summarization

## 🧪 Testing

### Test Structure
```
tests/
├── unit/           # Unit tests
│   ├── test_backup.bats
│   ├── test_memory_rw.bats
│   ├── test_current_task.bats
│   └── test_setup.bats
├── integration/    # Integration tests
│   ├── test_memory_backup_pipeline.bats
│   ├── test_resilience.bats
│   ├── test_retry_escalation.bats
│   └── test_setup_parity.bats
└── functionality/  # Functional tests
    ├── test_functionality.md
    └── test_interruption.md
```

### Run Tests
```bash
scripts/run_tests.sh
```

## 🔍 Troubleshooting

### Agent Not Responding
- Check agent status
- Review `current_task.md` for interrupted tasks
- Check memory logs for errors

### Task Not Completing
- Review PLAN.md for issues
- Check TASKS.md for blocking problems
- Verify specialist agent access

### Memory Issues
- Run `scripts/memory_optimize.sh`
- Check disk space
- Review retention policy

## 📚 Documentation

- **System Design:** `docs/DESIGN.md` — Complete architecture
- **Integration Guide:** `docs/openclaw-integration.md` — OpenClaw-specific
- **Installation Guides:** `docs/install-*.md` — Environment-specific
- **Task List:** `docs/TASKS.md` — Complete task breakdown
- **Architecture:** `docs/ARCHITECTURE.md` — Infrastructure docs

## 🎯 Use Cases

### Software Development
```
You: "Add a new feature to the project"
→ Speak-er → Plan-er → Task-er → Review-er → Deploy-er → Test-er
→ Complete feature with tests and documentation
```

### Research
```
You: "Research and summarize recent advances in ML"
→ Speak-er → Plan-er (research strategy) → Task-er (data gathering)
→ Specialists (read papers, summarize) → Review-er → Final report
```

### Project Management
```
You: "Organize my TODO list and prioritize tasks"
→ Speak-er → Plan-er (prioritization strategy) → Task-er (task breakdown)
→ Specialists (research best practices) → Review-er → Updated TODO list
```

### Content Creation
```
You: "Write a blog post about Python async programming"
→ Speak-er → Plan-er (outline) → Task-er (draft sections)
→ Prompt-er (optimize) → Test-er (review for errors) → Final post
```

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
1. Check `docs/DESIGN.md` for architecture questions
2. Review `docs/TASKS.md` for complete task list
3. Consult `docs/ARCHITECTURE.md` for infrastructure questions
4. Check `CHANGES.md` for recent updates

## 🎭 About Parlei

**Parlei** (parley) means "a discussion between parties" — like a parliamentary debate. Just as a parliament brings together different voices to make decisions, Parlei brings together specialized AI agents to complete complex tasks.

**The Parliament of Owls:**
- Each owl represents a specialist agent
- The Spirit of the Forest guides the Parliament (you)
- Decisions are made through coordinated debate and collaboration

**Always the Owl, now the Parliament!** 🦉

---

**Repository:** https://github.com/DrClawd/parlei
**Created:** 2026-03-27
**License:** Open Source
**Maintainer:** DrClawd (@DrClawd)