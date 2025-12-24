---
name: membase
description: "Git-native project memory system for storing and retrieving project decisions, implementation details, and documentation across coding sessions. Use when starting work on a topic, making design decisions, implementing features, or debugging issues that might have prior context. Claude should proactively query memories before implementing features or making architectural decisions to maintain consistency."
---

# Membase: Git-Native Project Memory

**TL;DR:** Store project decisions and context with `scripts/mb add`, retrieve with `scripts/mb query`, maintain consistency across sessions.

## What is Membase?

Membase is a git-native project memory system that stores project knowledge in simple text files (`.membase/`). It uses multi-dimensional tagging to organize information and enables efficient context retrieval across sessions.

**Core principle:** Store decisions and context so they're never lost between sessions. Retrieve them when needed to avoid re-solving problems or contradicting earlier decisions.

## Quick Start

```bash
# Initialize membase in your project
scripts/mb init

# Add your first topic
scripts/mb dims add topic authentication

# Store a decision
scripts/mb add -s "JWT auth with 24h expiry" \
  -c "Using JWT for stateless authentication. Tokens expire in 24h." \
  topic=authentication phase=decision

# Query decisions before implementing
scripts/mb query --topic authentication --phase decision
```

## When to Store Memories

Proactively store memories using `scripts/mb add` when:

1. **Design decisions are made**
   - Architecture choices (REST vs GraphQL, state management approach)
   - Technology selections (database choice, library decisions)
   - Pattern decisions (error handling strategy, testing approach)

2. **Implementation approaches are chosen**
   - Algorithm selections
   - Data structure decisions
   - Integration patterns

3. **Gotchas or workarounds are discovered**
   - Edge cases handled in specific ways
   - Framework quirks or limitations
   - Performance optimizations

4. **User states preferences or requirements**
   - Explicit project requirements
   - Coding style preferences
   - Workflow preferences

5. **Key file locations or patterns are established**
   - Where specific types of code live
   - Naming conventions
   - Module organization patterns

## When to Retrieve Memories

Query memories using `scripts/mb query` when:

1. **Starting work on a topic**
   - Check what's already decided before implementing
   - Understand context from previous sessions
   - Avoid contradicting earlier decisions

2. **User asks about previous decisions**
   - "What did we decide about authentication?"
   - "Why did we choose PostgreSQL?"
   - "How is error handling implemented?"

3. **Implementing something that might have prior context**
   - Before adding a new feature in an existing area
   - When uncertain about existing patterns
   - To maintain consistency with earlier work

4. **Debugging or troubleshooting**
   - Check if similar issues were encountered before
   - Review relevant implementation decisions
   - Understand context around problematic code

## Multi-Dimensional Tagging

Membase organizes memories with two dimensions:

### 1. topic (Project-specific subject areas)

Define topics based on your project's architecture. Common examples:

- `authentication` - Auth mechanisms, session management, tokens
- `database` - Schema, migrations, ORM choices
- `api` - Endpoints, REST/GraphQL decisions, versioning
- `frontend` - UI frameworks, state management, routing
- `deployment` - CI/CD, hosting, infrastructure

Add topics as needed:
```bash
scripts/mb dims add topic authentication
scripts/mb dims add topic database
```

### 2. phase (Workflow stage)

Pre-populated with defaults to track the decision lifecycle:

- `requirements` - User requirements and specifications
- `decision` - Architectural or design decisions ⭐ **Most important**
- `planning` - Implementation planning notes
- `backend-implementation` - Backend code details and locations
- `frontend-implementation` - Frontend code details and locations
- `testing` - Testing strategies and test details
- `documentation` - Documentation notes and patterns
- `troubleshooting` - Known issues and their solutions
- `deployment` - Deployment configurations and notes

**Custom dimensions:**
```bash
scripts/mb dims add-dim priority "Task priority level"
scripts/mb dims add priority high
scripts/mb dims add priority critical
```

## Common Usage Patterns

### Pattern 1: Recording Architectural Decisions

When making technology or architecture choices:

```bash
scripts/mb add \
  -s "PostgreSQL for main database" \
  -c "Chose PostgreSQL over MySQL for better JSON support and PostGIS if needed later. Using SQLAlchemy as ORM. Connection pool sized at 10-20 based on expected load." \
  topic=database phase=decision
```

### Pattern 2: Documenting Implementation Details

When implementing features:

```bash
scripts/mb add \
  -s "User model in src/models/user.py" \
  -c "User model includes: username, email, password_hash, created_at, updated_at. Email is unique. Passwords hashed with bcrypt (12 rounds). Includes methods for password verification and token generation." \
  topic=authentication phase=backend-implementation
```

### Pattern 3: Capturing Gotchas and Edge Cases

When discovering important edge cases:

```bash
scripts/mb add \
  -s "API rate limiting uses Redis with sliding window" \
  -c "Implemented sliding window rate limiting in src/middleware/ratelimit.py. Key: 'ratelimit:user:{id}:{endpoint}'. Window: 60 seconds. Limit: 100 requests. IMPORTANT: Must call redis.expire() after incrementing to prevent memory leak." \
  topic=api phase=troubleshooting
```

### Pattern 4: Querying Before Implementing

Before starting implementation:

```bash
# Check all decisions for a topic
scripts/mb query --topic authentication --phase decision

# Search for specific keywords
scripts/mb query --search "JWT"

# Get full context on a specific memory
scripts/mb query --id abc12345
```

### Pattern 5: Team Workflow Integration

Membase works naturally with git:

```bash
# After adding memories during development
git add .membase/
git commit -m "Document authentication decisions"
git push

# Team members get memories automatically
git pull  # Receives shared project context
```

## Best Practices

### What to Store

**DO store:**
- Decisions with rationale (the "why" behind choices)
- Implementation patterns and conventions
- Known limitations and workarounds
- File locations and organization patterns
- Configuration choices and their reasoning
- Integration details and API contracts

**DON'T store:**
- Code snippets (git is for code)
- Trivial decisions (e.g., "added a comment")
- Temporary notes or WIP thoughts
- Information that changes frequently

### Writing Effective Summaries

Summaries appear in listings—make them scannable and specific:

```bash
# ✓ Good: Specific and clear
-s "JWT auth with 24h expiry and refresh tokens"

# ✗ Bad: Vague
-s "Authentication stuff"

# ✓ Good: Identifies location
-s "Rate limiting middleware in src/middleware/ratelimit.py"

# ✗ Bad: No location context
-s "Rate limiting"
```

**Summary guidelines:**
- Maximum 100 characters
- Include key details (technology, file location, or main concept)
- Use consistent terminology
- Front-load important information

### Writing Effective Content

Content provides context for future sessions—include the "why" and "how":

```bash
# ✓ Good: Includes rationale and details
-c "Chose JWT over sessions because the API needs to be stateless for horizontal scaling. Access tokens expire in 24h, refresh tokens in 7 days. Stored in HTTP-only cookies to prevent XSS. Implementation in src/auth/jwt.py uses PyJWT library."

# ✗ Bad: No context
-c "Using JWT for auth"
```

**Content guidelines:**
- Explain the reasoning behind decisions
- Include relevant file paths
- Mention alternatives considered
- Note any important constraints or trade-offs
- Add specific configuration values

### Consistent Tagging Strategy

Use tags systematically to make queries predictable:

```bash
# Decision about authentication
topic=authentication phase=decision

# Implementation of authentication
topic=authentication phase=backend-implementation

# Problem and solution with authentication
topic=authentication phase=troubleshooting
```

## Workflow Integration

### Session Start

Begin coding sessions by reviewing context:

```bash
# Review recent work
scripts/mb query --limit 10

# Check relevant area
scripts/mb query --topic <area-you-are-working-on>

# View project coverage
scripts/mb stats
```

### During Implementation

Integrate membase into your development flow:

```bash
# BEFORE implementing: Check for existing decisions
scripts/mb query --topic <area> --phase decision

# AFTER deciding: Store the decision
scripts/mb add -s "..." -c "..." topic=<area> phase=decision

# AFTER implementing: Document key details
scripts/mb add -s "..." -c "..." topic=<area> phase=backend-implementation

# WHEN troubleshooting: Check for known issues
scripts/mb query --topic <area> --phase troubleshooting
```

### Session End

Capture any final insights:

```bash
# Store discoveries made during implementation
scripts/mb add -s "..." -c "..." <tags>

# Verify important items were captured
scripts/mb stats
```

## Claude Code Integration

**For Claude Code:**

### When to Proactively Store

Store memories automatically when:
- A significant decision is made during conversation
- Implementation patterns are established
- Gotchas or workarounds are discovered
- User states explicit preferences

### When to Proactively Retrieve

Query memories before:
- Starting work on a new feature
- Making architectural decisions
- Implementing in an area that might have context
- Answering questions about previous decisions

### Example Interaction

```
User: "Let's add user authentication"

Claude: "Let me check if there are any existing decisions about authentication."
[Runs: scripts/mb query --topic authentication --phase decision]

Claude: "I found a previous decision to use JWT auth with 24h expiry.
I'll implement following this pattern..."
```

### Maintaining Consistency

1. **Always check membase before architectural decisions**
2. **Reference stored decisions when relevant** (mention memory ID)
3. **Suggest updating memories** when decisions change
4. **Proactively store new decisions** after user approval

## Examples

### Example 1: API Design Decision

```bash
scripts/mb add \
  -s "REST API using Flask-RESTful" \
  -c "Chose REST over GraphQL for simplicity and team familiarity. Using Flask-RESTful for routing. API versioning via URL path (/api/v1/...). JSON responses with standardized error format: {\"error\": {\"code\": \"...\", \"message\": \"...\"}}. Error codes follow HTTP status codes." \
  topic=api phase=decision
```

### Example 2: Database Schema Documentation

```bash
scripts/mb add \
  -s "Orders table schema in migrations/002_orders.sql" \
  -c "Orders table includes: id (UUID), user_id (FK to users), status (enum: pending/processing/completed/cancelled), total_amount (decimal 10,2), created_at, updated_at. Composite index on (user_id, status) for dashboard queries. Status transitions logged in order_history table." \
  topic=database phase=backend-implementation
```

### Example 3: Troubleshooting Discovery

```bash
scripts/mb add \
  -s "Fix for race condition in order processing" \
  -c "Discovered race condition when multiple workers processed same order simultaneously. Fixed by adding SELECT FOR UPDATE in src/workers/order_processor.py:45. Also added unique constraint on orders.processing_lock_id to prevent duplicates. Workers now retry with exponential backoff on lock contention." \
  topic=api phase=troubleshooting
```

### Example 4: Frontend Pattern

```bash
scripts/mb add \
  -s "Form validation using Formik + Yup" \
  -c "Standardized on Formik for form handling and Yup for validation schemas across all forms. Pattern: Create schema in src/validation/schemas/, import and use in components with useFormik hook. See src/components/LoginForm.tsx for reference implementation. Validation runs on blur and submit." \
  topic=frontend phase=frontend-implementation
```

### Example 5: Deployment Configuration

```bash
scripts/mb add \
  -s "Production deployment on AWS ECS Fargate" \
  -c "Deploying via AWS ECS Fargate with auto-scaling (min 2, max 10 tasks). Load balancer health checks on /health endpoint every 30s. Environment variables managed via AWS Parameter Store. Database credentials rotated via Secrets Manager. CI/CD pipeline defined in .github/workflows/deploy.yml triggers on main branch pushes." \
  topic=deployment phase=deployment
```

## Tips

- **Start simple**: Begin with 3-5 core topics, expand as needed
- **Be specific**: Detailed summaries make memories discoverable
- **Tag consistently**: Consistent tagging improves query effectiveness
- **Review regularly**: `scripts/mb stats` shows coverage gaps
- **Update when needed**: `scripts/mb edit <id>` keeps info current
- **Delete when obsolete**: `scripts/mb delete <id>` removes outdated info
- **Search liberally**: `scripts/mb query --search` is powerful for keywords

## Command Reference

```bash
# Initialize
scripts/mb init

# Add memory
scripts/mb add -s "summary" -c "content" dim=val [dim=val...]

# Query
scripts/mb query [--topic val] [--phase val] [--search "text"]
scripts/mb query --id <prefix>
scripts/mb query --all
scripts/mb query --json         # JSON output
scripts/mb query --full          # Force detailed view
scripts/mb query --brief         # Force summary view
scripts/mb query --limit N       # Limit results (default: 50)

# Dimensions
scripts/mb dims                          # List all
scripts/mb dims add <dimension> <value>  # Add value to dimension
scripts/mb dims add-dim <name> [desc]    # Create new dimension

# Edit
scripts/mb edit <id> [-s "new summary"] [-c "new content"] [dim=val...]

# Delete
scripts/mb delete <id> [-y]              # -y skips confirmation

# Stats
scripts/mb stats                         # Show memory counts by dimension
```

---

**Remember:** Membase keeps your project context alive across sessions, ensuring decisions aren't lost and patterns stay consistent. Query before implementing, store after deciding.
