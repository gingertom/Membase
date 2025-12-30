# Membase

**Git-native project memory for AI coding assistants**

Membase is a simple, git-friendly project memory system that helps AI coding assistants (like Claude Code) maintain context across sessions. It stores decisions, implementation details, and gotchas in plain text files that version naturally with your code.

## The Problem

When working with AI coding assistants across multiple sessions, important context gets lost:

- 🤔 "Why did we choose PostgreSQL over MySQL?"
- 🔄 "We already decided on JWT auth, but the AI doesn't remember"
- 🐛 "This bug was fixed before, but the solution isn't documented"
- 🎨 "What naming conventions did we establish?"

Without persistent memory, you waste time:
- Re-explaining decisions
- Re-solving problems
- Making inconsistent choices
- Searching through git history

## The Solution

Membase provides **persistent, queryable memory** that:

✅ **Lives in git** - No databases, no sync issues, just text files
✅ **Merges cleanly** - JSONL format prevents merge conflicts
✅ **Tags intelligently** - Multi-dimensional organization (topic × phase)
✅ **Queries fast** - Find relevant context in milliseconds
✅ **Stays simple** - Single Python script, zero dependencies

## Why Membase?

### Git-Native Design

Traditional approaches use SQLite or large JSON files that create merge conflicts. Membase uses:

- **JSONL format** - One memory per line, independent changes merge cleanly
- **UUID sorting** - Changes spread across file, reducing conflicts
- **Separate schema** - Dimension changes don't conflict with data changes
- **No gitignore** - Everything is committed, no hidden state

### Multi-Dimensional Organization

Organize memories by **topic** (what area) and **phase** (what stage):

```
topic=authentication phase=decision         → "Why JWT?"
topic=authentication phase=implementation   → "Where's the code?"
topic=authentication phase=troubleshooting  → "Known issues?"
```

Query precisely: "Show me all database decisions" or "Find API troubleshooting notes"

### Built for AI Assistants

Membase helps AI assistants:

- **Query before implementing** - Check existing decisions
- **Store after deciding** - Remember for next time
- **Maintain consistency** - Follow established patterns
- **Learn from gotchas** - Don't repeat mistakes

## Installation

No installation needed! Just copy the script:

```bash
# Clone this repo or copy scripts/mb to your project
curl -o scripts/mb https://raw.githubusercontent.com/gingertom/Membase/main/scripts/mb
chmod +x scripts/mb
```

**Requirements:** Python 3.7+ (uses only standard library)

## Quick Start

### 1. Initialize

```bash
scripts/mb init
```

Creates `.membase/` directory with:
- `schema.json` - Dimension definitions
- `memories.jsonl` - Memory storage

### 2. Add Topics

Define areas relevant to your project:

```bash
scripts/mb dims add topic authentication
scripts/mb dims add topic database
scripts/mb dims add topic api
```

### 3. Store a Decision

```bash
scripts/mb add \
  -s "Using JWT for authentication" \
  -c "Chose JWT over sessions for stateless API. 24h expiry, refresh tokens for 7 days. Stored in HTTP-only cookies." \
  topic=authentication phase=decision
```

### 4. Query Before Implementing

```bash
# What did we decide about authentication?
scripts/mb query --topic authentication --phase decision

# Search for specific details
scripts/mb query --search "JWT"

# See everything
scripts/mb query --all
```

### 5. Commit to Git

```bash
git add .membase/
git commit -m "Document authentication decision"
git push
```

Team members automatically get the context when they pull!

## Key Features

### Smart Querying

```bash
# By dimension
scripts/mb query --topic database --phase decision

# Full-text search
scripts/mb query --search "PostgreSQL"

# By ID prefix
scripts/mb query --id abc123

# JSON output for scripting
scripts/mb query --all --json
```

### Adaptive Output

- **≤5 results** → Shows full details automatically
- **>5 results** → Shows brief summaries (ID + tags + summary)
- Override with `--full` or `--brief`

### Validation & Typo Detection

```bash
$ scripts/mb add -s "Test" -c "..." topik=api phase=decision
✗ Unknown dimension 'topik'. Did you mean: topic?

$ scripts/mb add -s "Test" -c "..." topic=api phase=decission
✗ Unknown value 'decission' for dimension 'phase'. Did you mean: decision?
```

### Multi-Dimensional Tagging

**Default dimensions:**

- **topic** - Project-specific areas (you define: authentication, database, api, etc.)
- **phase** - Workflow stage (pre-populated):
  - `decision` - Architectural/design decisions
  - `backend-implementation` - Backend code details
  - `frontend-implementation` - Frontend code details
  - `troubleshooting` - Known issues and solutions
  - `planning`, `requirements`, `testing`, `documentation`, `deployment`

**Custom dimensions:**

```bash
scripts/mb dims add-dim priority "Task priority"
scripts/mb dims add priority high
scripts/mb dims add priority critical
```

### Statistics

```bash
$ scripts/mb stats
Total memories: 12

phase:
  decision: 5
  backend-implementation: 4
  troubleshooting: 3

topic:
  authentication: 4
  database: 5
  api: 3
```

## Usage Patterns

### For Developers

**Session start:**
```bash
scripts/mb query --all --limit 5     # What was I working on?
scripts/mb query --topic <area>      # Context for today's work
```

**During development:**
```bash
scripts/mb query --topic <area> --phase decision  # Check decisions
scripts/mb add -s "..." -c "..." <tags>           # Store new context
```

**Code review:**
```bash
scripts/mb query --topic <pr-area>   # Check if decision is documented
```

### For AI Assistants (Claude Code)

Membase includes a skill file (`SKILL.md`) that teaches Claude Code to:

1. **Query proactively** - Check for existing decisions before implementing
2. **Store automatically** - Suggest storing decisions after they're made
3. **Maintain consistency** - Reference stored context when relevant
4. **Update when needed** - Keep memories current as projects evolve

See [SKILL.md](SKILL.md) for Claude Code integration details.

## Common Use Cases

### Document Architectural Decisions

```bash
scripts/mb add \
  -s "Microservices architecture with event bus" \
  -c "Moving to microservices. Services communicate via RabbitMQ event bus. Each service has its own database (no shared DB). API gateway handles routing and auth. Chose this for independent scaling and deployment." \
  topic=architecture phase=decision
```

### Capture Implementation Details

```bash
scripts/mb add \
  -s "User service in services/user/" \
  -c "User service handles: registration, login, profile updates. Database: PostgreSQL. API: REST on port 8001. Auth: JWT validation via shared secret. Dockerfile for containerization." \
  topic=backend phase=backend-implementation
```

### Record Troubleshooting Solutions

```bash
scripts/mb add \
  -s "Fix: Database connection pool exhaustion" \
  -c "Issue: App crashed under load due to connection pool exhaustion. Solution: Increased pool size from 10 to 50, added connection timeout of 30s. Monitor with pg_stat_activity. File: src/database.py:15" \
  topic=database phase=troubleshooting
```

### Track Requirements

```bash
scripts/mb add \
  -s "API rate limiting: 100 req/min per user" \
  -c "Product requirement: Rate limit API to 100 requests per minute per authenticated user. Return 429 with Retry-After header. Admin users exempt from limits." \
  topic=api phase=requirements
```

## File Structure

```
your-project/
├── .membase/
│   ├── schema.json      # Dimensions and allowed values
│   └── memories.jsonl   # One memory per line, sorted by UUID
└── scripts/
    └── mb              # The membase CLI tool
```

## Commands

### Essential

```bash
scripts/mb init                                    # Initialize .membase/
scripts/mb add -s "summary" -c "content" <tags>    # Add memory
scripts/mb query [--topic X] [--phase Y]           # Query memories
scripts/mb query --search "keyword"                # Full-text search
scripts/mb stats                                   # Show statistics
```

### Management

```bash
scripts/mb dims                                    # List dimensions
scripts/mb dims add <dimension> <value>            # Add value to dimension
scripts/mb edit <id> -s "new summary"              # Edit memory
scripts/mb delete <id>                             # Delete memory
```

See [REFERENCE.md](REFERENCE.md) for complete command reference and advanced usage.

## Documentation

- **[SKILL.md](SKILL.md)** - Concise guide for Claude Code integration
- **[REFERENCE.md](REFERENCE.md)** - Comprehensive reference with examples and advanced usage

## Git Workflow

### Individual Work

```bash
# Make changes and store context
scripts/mb add -s "..." -c "..." <tags>

# Commit together with code
git add .membase/ src/
git commit -m "Add authentication + document decision"
git push
```

### Team Collaboration

```bash
# Pull changes from team
git pull  # Automatically merges memories

# If conflicts, accept both (different memories)
# File auto-sorts, so merge both changes

# Review team's decisions
scripts/mb query --all --limit 10
```

### Feature Branches

Memories stay with the code:

```bash
git checkout -b feature/payments
scripts/mb add -s "Stripe integration" -c "..." topic=payments phase=decision
git commit -am "Add payments feature + decision"
git push

# PR reviewers see both code AND context
# When merged, memory comes with the feature
```

## Design Philosophy

### Simplicity Over Features

- **No database** - Just text files
- **No dependencies** - Pure Python standard library
- **No configuration** - Sensible defaults
- **No network** - Everything is local and in git

### Git-First

- **Commit everything** - `.membase/` is part of the project
- **Merge-friendly** - JSONL format handles concurrent changes
- **Version control** - Full history in git
- **Team-ready** - Shared context across all contributors

### AI-Assistant Friendly

- **Queryable** - Fast, precise context retrieval
- **Taggable** - Multi-dimensional organization
- **Discoverable** - Search finds relevant context
- **Maintainable** - Edit and delete outdated info

## FAQ

**Q: Why not just use git commit messages?**
A: Commit messages are chronological and hard to query. "Show me all database decisions" is instant with membase, impossible with git log.

**Q: Why not use a wiki or Notion?**
A: External tools require syncing and don't version with code. Membase lives in the repo and merges naturally.

**Q: Why not SQLite?**
A: SQLite binaries don't merge. Two developers can't add memories concurrently without conflicts. JSONL merges cleanly.

**Q: How big can it get?**
A: Suitable for hundreds to thousands of memories. For very large projects, archive old memories to a separate file.

**Q: Does it work with other AI assistants?**
A: Yes! The CLI works with any AI. The SKILL.md file is Claude Code-specific, but the concept applies to any assistant.

**Q: Can I use it without AI?**
A: Absolutely! It's useful for personal knowledge management and team documentation.

## Examples

See [REFERENCE.md](REFERENCE.md) for detailed examples including:

- API design decisions
- Database schema documentation
- Troubleshooting discoveries
- Frontend patterns
- Deployment configurations
- Team workflows
- Scripting with membase

## Contributing

This is a personal project, but suggestions and improvements are welcome! File an issue or submit a PR.

## License

MIT License - use freely in your projects.

## Credits

Created to solve the "context loss" problem when working with AI coding assistants across multiple sessions.

---

**Remember:** Store decisions, query before implementing, keep context alive across sessions.
