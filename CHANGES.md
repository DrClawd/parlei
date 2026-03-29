# Changes — Parlei OpenClaw Integration Fork

## Overview

This fork adds **OpenClaw multi-agent orchestration** to Parlei, enabling dedicated routing between TUI and Discord channels, as requested by Colby.

## New Files Added

### 1. Orchestrator Agent
- `shared/orchestrator/orchestrator.md`
  - Dedicated Claude Sonnet 4.6 orchestrator agent
  - Handles TUI/Discord channel routing
  - Manages multi-agent coordination
  - Controls lateral communication grants

### 2. Routing Configuration
- `shared/tools/orchestrator_routing.json`
  - Orchestrator model configuration
  - Channel routing rules (TUI → Orchestrator → Speak-er)
  - Agent enablement and requirements
  - Lateral communication grant definitions

### 3. Prompt Templates
- `shared/orchestrator/prompts.md`
  - Task assessment templates
  - Discord/TUI formatting rules
  - Multi-agent coordination prompts
  - Escalation handling templates

### 4. Integration Documentation
- `docs/openclaw-integration.md`
  - Architecture diagrams
  - OpenClaw integration guide
  - Usage examples
  - Troubleshooting section

### 5. OpenClaw README
- `README-OPENCLAW.md`
  - Comprehensive OpenClaw integration guide
  - Quick start instructions
  - Agent roster documentation
  - Configuration examples

### 6. Changes Log
- `CHANGES.md` (this file)
  - Documents all modifications
  - Tracks new components
  - Provides upgrade path

## Modified Files

### 1. OpenClaw Bootstrap
- `bootstraps/OPENCLAW.md`
  - Added orchestrator integration instructions
  - Updated loading sequence to include Orchestrator check
  - Added multi-agent coordination guidance
  - Updated channel-specific formatting rules
  - Added orchestration status checking commands

**Changes:**
- Added step 1: "Check for existing orchestrator"
- Added steps 8-9: Orchestrator configuration and routing checks
- Added section: "Orchestrator Integration" with workflow diagrams
- Updated "Orchestrator-Specific Notes" with OpenClaw session management commands
- Enhanced "Agent Communication Protocol" with JSON examples

## Core Concepts

### Orchestrator Agent

The **Orchestrator** is a dedicated Claude Sonnet 4.6 agent that:
- **Routes tasks** between TUI and Discord channels
- **Assesses complexity** and determines routing
- **Coordinates multi-agent** workflows
- **Manages lateral communication** grants
- **Maintains task registry** for tracking

**Default Entry Point for OpenClaw:**
```
TUI/Discord → Orchestrator → Speak-er → Specialists
```

### Task Routing

**Simple Request:**
```
TUI/Discord → Orchestrator → Speak-er (direct)
```

**Complex Request:**
```
TUI/Discord → Orchestrator → Speak-er → Plan-er → Task-er
```

**Discord Reply:**
```
Discord → Orchestrator → Speak-er (with Discord formatting)
```

## Key Components

### Routing Configuration

```json
{
  "orchestrator": {
    "name": "orchestrator",
    "model": "anthropic/claude-sonnet-4.6",
    "enabled": true
  },
  "routing": {
    "tui": {
      "channel": "tui",
      "primaryAgent": "orchestrator"
    },
    "discord": {
      "channel": "discord",
      "primaryAgent": "orchestrator"
    }
  }
}
```

### Multi-Agent Coordination

```
Orchestrator → Speak-er → Plan-er → Task-er → Result
Orchestrator monitors → reports → returns to channel
```

## Usage

### Starting the System

```bash
# 1. Clone the forked repository
git clone https://github.com/DrClawd/parlei.git
cd parlei

# 2. Run OpenClaw bootstrap
scripts/setup.sh openclaw

# 3. Spawn the Orchestrator agent
sessions_spawn --task "Initialize Parlei Orchestrator" --agentId orchestrator

# 4. Start using Parlei in TUI or Discord
```

### Task Examples

**TUI (Simple):**
```
User: "Summarize my meeting notes"

Orchestrator → Speak-er → Returns summary
```

**Discord (Complex):**
```
User: "Plan a weekend hiking trip and create a packing list"

Orchestrator → Speak-er → Plan-er → Task-er → Comprehensive plan
```

## Agent Communication

All agents use OpenClaw's session-based communication:

**Request Format:**
```json
{
  "from": "orchestrator",
  "to": "speak-er",
  "request_id": "req-orchestrator-20260327-001",
  "items": [
    {
      "id": 1,
      "type": "routing",
      "description": "Route TUI request to Speak-er"
    }
  ]
}
```

**Response Format:**
```json
{
  "from": "speak-er",
  "to": "orchestrator",
  "request_id": "req-orchestrator-20260327-001",
  "items": [
    {
      "id": 1,
      "status": "routed",
      "notes": "Task routed to Speak-er"
    }
  ]
}
```

## Channel-Specific Formatting

### Discord
- Wrap links: `<https://example.com>`
- Use bullet lists, not tables
- Keep responses concise (1-2 paragraphs)
- Thread replies for follow-ups

### TUI
- Use headers: ## Section, ### Subsection
- Markdown tables when appropriate
- Clear section breaks

## Integration with Existing Parlei

This fork maintains **100% compatibility** with the existing Parlei system:

- ✅ All 10 specialist agents unchanged
- ✅ Shared memory and configuration intact
- ✅ Nightly optimization and backup unchanged
- ✅ All bootstrap files for Claude, Augment, Codex unchanged
- ✅ Protocol and tooling unchanged
- ✅ Only adds Orchestrator layer on top

**Backward Compatible:**
- Can still use Parlei directly without Orchestrator (open `CLAUDE.md` directly)
- All existing scripts and tools work identically
- Existing sessions continue to function

**New Capabilities:**
- Multi-channel routing (TUI + Discord)
- Dedicated orchestrator (Claude Sonnet 4.6)
- Cross-session coordination
- Enhanced task tracking

## Configuration

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

## Troubleshooting

### Orchestrator Not Responding

```bash
# Check orchestrator status
sessions_list --kinds subagent

# Check routing config
cat shared/tools/orchestrator_routing.json
```

### Task Not Routing

1. Check channel type detection in logs
2. Verify prompt templates in `shared/orchestrator/prompts.md`
3. Review routing rules in `shared/tools/orchestrator_routing.json`

### Cross-Channel Duplication

1. Check task registry for existing tasks
2. Ensure Orchestrator prevents duplicate execution
3. Review lateral communication grants

## Files Summary

### New Files (8)
- `shared/orchestrator/orchestrator.md` (3,620 bytes)
- `shared/orchestrator/prompts.md` (3,436 bytes)
- `shared/tools/orchestrator_routing.json` (1,850 bytes)
- `docs/openclaw-integration.md` (7,945 bytes)
- `README-OPENCLAW.md` (10,421 bytes)
- `CHANGES.md` (this file)
- `bootstraps/OPENCLAW.md` (modified, 6,782 bytes)
- `memory/2026-03-27.md` (updated with session notes)

**Total New Content:** ~37,054 bytes

### Modified Files (1)
- `bootstraps/OPENCLAW.md` (added orchestrator integration)

## Testing

### Verify Orchestrator

```bash
# Spawn orchestrator
sessions_spawn --task "Initialize Parlei Orchestrator" --agentId orchestrator

# Check it's running
sessions_list --kinds subagent
```

### Test Routing

**TUI Test:**
```bash
# In TUI session
Message: "Summarize my notes"
Expected: Orchestrator routes → Speak-er → summary
```

**Discord Test:**
```bash
# In Discord
Message: "Plan a trip"
Expected: Orchestrator routes → multi-agent → comprehensive plan
```

## Upgrade Path

### From Original Parlei

1. **Backup existing:**
   ```bash
   scripts/backup.sh
   ```

2. **Fork the repository:**
   ```bash
   git clone https://github.com/ColbyWanShinobi/parlei.git drclaw-parlei
   ```

3. **Apply changes:**
   ```bash
   cp -r shared/ shared-backup/
   cp -r shared-new/* shared/
   ```

4. **Update OpenClaw bootstrap:**
   ```bash
   # Edit bootstraps/OPENCLAW.md
   ```

5. **Run setup:**
   ```bash
   scripts/setup.sh openclaw
   ```

6. **Spawn Orchestrator:**
   ```bash
   sessions_spawn --agentId orchestrator
   ```

### From Previous Fork

If you already have the fork:

1. **Pull changes:**
   ```bash
   git pull origin main
   ```

2. **Restart sessions:**
   ```bash
   sessions_spawn --agentId orchestrator
   ```

3. **Restart OpenClaw framework**

## Future Enhancements

Planned for future versions:

- [ ] Dashboard for agent activity monitoring
- [ ] Automatic task archival and summaries
- [ ] Advanced task prioritization
- [ ] Multi-region / multi-server coordination
- [ ] Real-time agent health monitoring
- [ ] Web UI (SvelteKit-based)

## Support

For integration issues:
1. See `docs/openclaw-integration.md` for detailed guide
2. Review `README-OPENCLAW.md` for quick start
3. Check `shared/tools/orchestrator_routing.json` for configuration

---

**Fork Owner:** DrClawd (@DrClawd)
**Original Repository:** ColbyWanShinobi/parlei
**OpenClaw Version:** Requires OpenClaw with multi-agent support
**Created:** 2026-03-27

🎉 **Parlei now works with OpenClaw's multi-agent framework!** 🦉
## Additional Tools
- `shared-discord-post-format`
  - Mirrors the event header/day formatting used by `scripts/weekender.py`
  - Builds the same native embed payloads (`build_event_embed`) and headers (`Weekend Events` / `Upcoming Events`)
  - Accepts JSON event lists via stdin or `--events-file`
  - Useful for debugging or copying the exact Discord format outside the cron job

### 3. Discord Routing Default
- `shared/tools/orchestrator_routing.json`
  - Set both the TUI and Discord fallback agents to the orchestrator so every Discord channel defaults to the orchestrator rather than the legacy `main` agent

### 4. Speak-er/Orchestrator Merge
- `shared/orchestrator/orchestrator.md`, `bootstraps/OPENCLAW.md`, `docs/openclaw-integration.md`
  - Documented that the orchestrator now *is* Speak-er when it is the user-facing entry point
  - Added instructions so the orchestrator loads Speak-er’s bootstrap, personality, and memory context for direct channel replies
  - Clarified the main entry point terminology to reflect a hybrid orchestrator/Speak-er agent
