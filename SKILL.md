# Membase: Git-Native Project Memory

**Usage:** Use membase to maintain persistent project context across coding sessions by storing and retrieving key decisions, implementation details, and documentation.

## What is Membase?

Membase is a git-native project memory system that stores project knowledge in simple text files (`.membase/`). It uses multi-dimensional tagging to organize information and enables efficient context retrieval across sessions.

**Core principle:** Store decisions and context so they're never lost between sessions. Retrieve them when needed to avoid re-solving problems.

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

## Usage Patterns

### Initial Setup

When starting a new project or adding membase to an existing one:

```bash
# Initialize membase
scripts/mb init

# Add project-specific topics
scripts/mb dims add topic authentication
scripts/mb dims add topic database
scripts/mb dims add topic api
scripts/mb dims add topic frontend
```

### Recording Decisions

When a significant decision is made:

```bash
scripts/mb add \
  -s "PostgreSQL for main database" \
  -c "Chose PostgreSQL over MySQL for better JSON support and PostGIS if needed later. Using SQLAlchemy as ORM. Connection pool sized at 10-20 based on expected load." \
  topic=database phase=decision
```

### Recording Implementation Details

When implementing a feature:

```bash
scripts/mb add \
  -s "User model in src/models/user.py" \
  -c "User model includes: username, email, password_hash, created_at, updated_at. Email is unique. Passwords hashed with bcrypt (12 rounds). Includes methods for password verification and token generation." \
  topic=authentication phase=backend-implementation
```

### Recording Gotchas

When discovering important edge cases:

```bash
scripts/mb add \
  -s "API rate limiting uses Redis with sliding window" \
  -c "Implemented sliding window rate limiting in src/middleware/ratelimit.py. Key: 'ratelimit:user:{id}:{endpoint}'. Window: 60 seconds. Limit: 100 requests. IMPORTANT: Must call redis.expire() after incrementing to prevent memory leak." \
  topic=api phase=backend-implementation
```

### Querying by Topic

Before implementing something new:

```bash
# Check what's been decided about authentication
scripts/mb query --topic authentication

# Check all database-related decisions
scripts/mb query --topic database --phase decision

# Search for specific keywords
scripts/mb query --search "JWT"
```

### Reviewing Specific Memories

When you need details on a particular decision:

```bash
# Using ID prefix (shown in brief listings)
scripts/mb query --id abc12345

# This shows the full content of that memory
```

## Multi-Dimensional Tagging

Membase uses two default dimensions:

1. **topic** - Project-specific subject areas (you define these)
   - Examples: authentication, database, api, frontend, deployment
   - Add values with: `scripts/mb dims add topic <name>`

2. **phase** - Workflow stage (pre-populated with defaults)
   - `requirements` - User requirements and specifications
   - `decision` - Architectural or design decisions
   - `planning` - Implementation planning notes
   - `backend-implementation` - Backend code details
   - `frontend-implementation` - Frontend code details
   - `testing` - Testing strategies and details
   - `documentation` - Documentation notes
   - `troubleshooting` - Known issues and solutions
   - `deployment` - Deployment configurations and notes

You can also add custom dimensions:

```bash
scripts/mb dims add-dim priority "Task priority level"
scripts/mb dims add priority high
scripts/mb dims add priority medium
scripts/mb dims add priority low
```

## Best Practices

### What to Store

**DO store:**
- Decisions with rationale
- Implementation patterns and conventions
- Known limitations and workarounds
- File locations and organization patterns
- Configuration choices
- Integration details

**DON'T store:**
- Code snippets (git is for code)
- Trivial decisions
- Temporary notes
- Work-in-progress thoughts

### Writing Good Summaries

Summaries appear in listings, so make them scannable:

```bash
# Good: Specific and clear
-s "JWT auth with 24h expiry and refresh tokens"

# Bad: Vague
-s "Authentication stuff"

# Good: Identifies location
-s "Rate limiting middleware in src/middleware/ratelimit.py"

# Bad: No location context
-s "Rate limiting"
```

### Writing Good Content

Content should provide context for future sessions:

```bash
# Good: Includes rationale and details
-c "Chose JWT over sessions because the API needs to be stateless for horizontal scaling. Access tokens expire in 24h, refresh tokens in 7 days. Stored in HTTP-only cookies to prevent XSS. Implementation in src/auth/jwt.py uses PyJWT library."

# Bad: No context
-c "Using JWT for auth"
```

### Tagging Strategy

Use tags consistently:

- **topic**: What area of the project (authentication, database, api, etc.)
- **phase**: What stage (decision, implementation, troubleshooting, etc.)

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

At the beginning of a coding session:

```bash
# Review recent memories
scripts/mb query --limit 10

# Check relevant topic
scripts/mb query --topic <current-area>

# Check statistics to understand project coverage
scripts/mb stats
```

### During Implementation

While coding:

```bash
# Before implementing: Check for existing decisions
scripts/mb query --topic <area> --phase decision

# After deciding: Store the decision
scripts/mb add -s "..." -c "..." topic=<area> phase=decision

# After implementing: Store key details
scripts/mb add -s "..." -c "..." topic=<area> phase=backend-implementation
```

### Session End

Before ending a session:

```bash
# Store any final decisions or gotchas discovered
scripts/mb add -s "..." -c "..." <tags>

# Quick stats check to ensure important items were captured
scripts/mb stats
```

## Git Integration

Membase is designed to work naturally with git:

- **Commit `.membase/` files**: They're part of the project
- **Merge-friendly**: JSONL format and UUID sorting minimize conflicts
- **No gitignore**: Everything is tracked
- **Team collaboration**: Shared memory across all contributors

```bash
# After adding memories
git add .membase/
git commit -m "Add authentication decision to membase"

# Memories sync with git push/pull
git push
```

## Examples

### Example 1: API Design Decision

```bash
scripts/mb add \
  -s "REST API using Flask-RESTful" \
  -c "Chose REST over GraphQL for simplicity. Using Flask-RESTful for routing. API versioning via URL (/api/v1/...). JSON responses with standardized error format: {\"error\": {\"code\": \"...\", \"message\": \"...\"}}" \
  topic=api phase=decision
```

### Example 2: Database Schema

```bash
scripts/mb add \
  -s "Orders table schema in migrations/002_orders.sql" \
  -c "Orders table includes: id (UUID), user_id (FK), status (enum), total_amount (decimal), created_at, updated_at. Status values: pending, processing, completed, cancelled. Indexes on user_id and status for common queries." \
  topic=database phase=backend-implementation
```

### Example 3: Troubleshooting

```bash
scripts/mb add \
  -s "Fix for race condition in order processing" \
  -c "Discovered race condition when multiple workers processed same order. Fixed by adding SELECT FOR UPDATE in src/workers/order_processor.py:45. Also added unique constraint on orders.processing_lock_id to prevent duplicates." \
  topic=api phase=troubleshooting
```

### Example 4: Frontend Pattern

```bash
scripts/mb add \
  -s "Form validation using Formik + Yup" \
  -c "Standardized on Formik for form handling and Yup for validation schemas. Pattern: Create schema in src/validation/schemas/, use in components with useFormik hook. Example in src/components/LoginForm.tsx." \
  topic=frontend phase=frontend-implementation
```

## Claude Code Integration

As Claude Code, you should:

1. **Proactively suggest storing memories** when:
   - A significant decision is made during the conversation
   - Implementation patterns are established
   - Gotchas or workarounds are discovered

2. **Proactively retrieve memories** when:
   - Starting work on a familiar topic
   - User asks about previous decisions
   - Implementing something that might have context

3. **Maintain consistency**:
   - Check membase before making architectural decisions
   - Reference stored decisions when they're relevant
   - Update memories if decisions change

4. **Example interaction**:
   ```
   User: "Let's add user authentication"
   Claude: "Let me check if there are any existing decisions about authentication."
   [runs: scripts/mb query --topic authentication]
   Claude: "I found a previous decision to use JWT auth with 24h expiry. I'll implement this pattern..."
   ```

## Tips

- **Start simple**: Begin with just a few topics, add more as needed
- **Be specific**: Good summaries make memories easy to find later
- **Tag consistently**: Consistent tagging makes queries more effective
- **Review regularly**: Use `scripts/mb stats` to see coverage
- **Update when needed**: Use `scripts/mb edit` if decisions change
- **Delete when obsolete**: Use `scripts/mb delete` for outdated information

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
scripts/mb query --json
scripts/mb query --full / --brief
scripts/mb query --limit N

# Dimensions
scripts/mb dims                          # List all
scripts/mb dims add <dimension> <value>  # Add value
scripts/mb dims add-dim <name> [desc]    # Add dimension

# Edit
scripts/mb edit <id> [-s "new summary"] [-c "new content"] [dim=val...]

# Delete
scripts/mb delete <id> [-y]

# Stats
scripts/mb stats
```

---

Membase keeps your project context alive across sessions, ensuring decisions aren't lost and patterns stay consistent.
