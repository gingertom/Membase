# Membase Reference Guide

Complete reference for membase commands, advanced usage patterns, and detailed examples.

## Table of Contents

- [Complete Command Reference](#complete-command-reference)
- [Detailed Examples](#detailed-examples)
- [Advanced Workflow Integration](#advanced-workflow-integration)
- [Git Integration](#git-integration)
- [Advanced Tagging Strategies](#advanced-tagging-strategies)
- [Tips and Tricks](#tips-and-tricks)

## Complete Command Reference

### Initialize

```bash
scripts/mb init
```

Creates `.membase/` directory with:
- `schema.json` - Dimension definitions and allowed values
- `memories.jsonl` - Memory storage (one JSON object per line)

### Add Memory

```bash
scripts/mb add -s "summary" -c "content" dimension=value [dimension=value...]
```

**Options:**
- `-s, --summary` - Summary text (required, max 100 characters)
- `-c, --content` - Full content (required)
- `dimension=value` - One or more tags (at least one required)

**Examples:**
```bash
scripts/mb add \
  -s "JWT auth with 24h expiry" \
  -c "Implementation details here..." \
  topic=authentication phase=decision

scripts/mb add \
  -s "User model in src/models/user.py" \
  -c "Complete field description..." \
  topic=database phase=backend-implementation
```

### Query Memories

```bash
scripts/mb query [options] [filters...]
```

**Filter Options:**
- `--topic VALUE` - Filter by topic dimension
- `--phase VALUE` - Filter by phase dimension
- `--search TEXT` - Full-text search (case-insensitive)
- `--id PREFIX` - Query specific memory by ID prefix
- `--all` - List all memories (same as no filters)

**Output Options:**
- `--json` - Output as JSON array
- `--full` - Force detailed view (shows full content)
- `--brief` - Force summary view (shows ID + summary only)
- `--limit N` - Limit results (default: 50)

**Adaptive Detail Level:**
- If results ≤ 5: Shows full content automatically
- If results > 5: Shows brief summaries automatically
- Override with `--full` or `--brief`

**Examples:**
```bash
# Filter by dimension
scripts/mb query --topic authentication
scripts/mb query --topic database --phase decision

# Full-text search
scripts/mb query --search "JWT"
scripts/mb query --search "PostgreSQL"

# Specific memory
scripts/mb query --id abc12345

# All memories with limit
scripts/mb query --all --limit 10

# JSON output for scripting
scripts/mb query --topic api --json
```

### Manage Dimensions

**List all dimensions and values:**
```bash
scripts/mb dims
```

**Add value to existing dimension:**
```bash
scripts/mb dims add <dimension> <value>
```

Examples:
```bash
scripts/mb dims add topic authentication
scripts/mb dims add topic database
scripts/mb dims add topic api
scripts/mb dims add topic frontend
scripts/mb dims add topic deployment
```

**Create new dimension:**
```bash
scripts/mb dims add-dim <name> [description]
```

Examples:
```bash
scripts/mb dims add-dim priority "Task priority level"
scripts/mb dims add priority high
scripts/mb dims add priority medium
scripts/mb dims add priority low

scripts/mb dims add-dim status "Implementation status"
scripts/mb dims add status planned
scripts/mb dims add status in-progress
scripts/mb dims add status completed
```

### Edit Memory

```bash
scripts/mb edit <id> [options]
```

**Options:**
- `-s, --summary TEXT` - New summary
- `-c, --content TEXT` - New content
- `dimension=value` - Update tags (merges with existing)

**Examples:**
```bash
# Update summary
scripts/mb edit abc12345 -s "New summary text"

# Update content
scripts/mb edit abc12345 -c "Updated content with more details..."

# Update tags
scripts/mb edit abc12345 topic=api

# Update multiple fields
scripts/mb edit abc12345 -s "New summary" -c "New content" phase=deployment
```

### Delete Memory

```bash
scripts/mb delete <id> [-y]
```

**Options:**
- `-y, --yes` - Skip confirmation prompt

**Examples:**
```bash
# With confirmation
scripts/mb delete abc12345

# Skip confirmation
scripts/mb delete abc12345 -y
```

### Show Statistics

```bash
scripts/mb stats
```

Shows:
- Total memory count
- Breakdown by each dimension
- Count per value in each dimension

## Detailed Examples

### Example 1: API Design Decision

**Scenario:** Choosing REST over GraphQL for the project API.

```bash
scripts/mb add \
  -s "REST API using Flask-RESTful" \
  -c "Chose REST over GraphQL for simplicity and team familiarity. Using Flask-RESTful for routing and request handling. API versioning via URL path (/api/v1/...). JSON responses with standardized error format: {\"error\": {\"code\": \"...\", \"message\": \"...\"}}. Error codes follow HTTP status codes. CORS enabled for web client at https://app.example.com." \
  topic=api phase=decision
```

**Why this is good:**
- States the decision clearly
- Explains the reasoning (simplicity, team familiarity)
- Documents the approach (Flask-RESTful, URL versioning)
- Includes specific details (error format, CORS config)

### Example 2: Database Schema Documentation

**Scenario:** Documenting the orders table schema.

```bash
scripts/mb add \
  -s "Orders table schema in migrations/002_orders.sql" \
  -c "Orders table includes: id (UUID primary key), user_id (FK to users), status (enum: pending/processing/completed/cancelled), total_amount (decimal 10,2), items (JSONB array of order items), created_at (timestamp), updated_at (timestamp). Composite index on (user_id, status) for dashboard queries showing user's active orders. Status transitions are logged in order_history table for audit trail. Soft deletes not used - cancelled orders kept with status=cancelled." \
  topic=database phase=backend-implementation
```

**Why this is good:**
- Specifies exact file location
- Lists all fields with types
- Documents indexes and their purpose
- Notes related tables
- Explains design decisions (no soft deletes)

### Example 3: Troubleshooting Discovery

**Scenario:** Finding and fixing a race condition in order processing.

```bash
scripts/mb add \
  -s "Fix for race condition in order processing" \
  -c "Discovered race condition when multiple workers processed same order simultaneously, causing duplicate charges. Fixed by adding SELECT FOR UPDATE in src/workers/order_processor.py:45 to acquire row-level lock. Also added unique constraint on orders.processing_lock_id (UUID generated at start of processing) to prevent duplicates at database level. Workers now retry with exponential backoff (2s, 4s, 8s) on lock contention. Tested with 10 concurrent workers processing same order - all but one fail gracefully." \
  topic=api phase=troubleshooting
```

**Why this is good:**
- Describes the problem clearly
- Documents the solution with file and line number
- Explains both code and database fixes
- Includes testing approach
- Notes retry behavior

### Example 4: Frontend Pattern

**Scenario:** Standardizing form validation across the application.

```bash
scripts/mb add \
  -s "Form validation using Formik + Yup" \
  -c "Standardized on Formik for form handling and Yup for validation schemas across all forms. Pattern: Create validation schema in src/validation/schemas/, import and use in components with useFormik hook. See src/components/LoginForm.tsx for reference implementation. Validation runs on blur and submit. Error messages shown inline below fields. Common validations (email, password strength, required fields) are in src/validation/common.ts for reuse. Form submission disabled while validating or submitting." \
  topic=frontend phase=frontend-implementation
```

**Why this is good:**
- Establishes clear pattern
- Points to reference implementation
- Documents validation triggers
- Notes reusable components
- Covers UX behavior

### Example 5: Deployment Configuration

**Scenario:** Documenting production deployment setup.

```bash
scripts/mb add \
  -s "Production deployment on AWS ECS Fargate" \
  -c "Deploying via AWS ECS Fargate with auto-scaling (min 2, max 10 tasks based on CPU >70%). Load balancer (ALB) health checks on /health endpoint every 30s, 2 consecutive failures trigger replacement. Environment variables managed via AWS Parameter Store. Database credentials rotated automatically via Secrets Manager (90-day rotation). Container images built and pushed by GitHub Actions on main branch pushes. CI/CD pipeline defined in .github/workflows/deploy.yml. Database migrations run as pre-deployment task. Zero-downtime deploys using rolling update strategy (25% at a time)." \
  topic=deployment phase=deployment
```

**Why this is good:**
- Complete deployment picture
- Specifies infrastructure (ECS Fargate, ALB)
- Documents scaling thresholds
- Notes security practices (secrets management)
- Explains deployment strategy

### Example 6: Requirements Documentation

**Scenario:** User requirement for password reset flow.

```bash
scripts/mb add \
  -s "Password reset requires email verification" \
  -c "User requirement: Password reset must send verification code to email. Code valid for 15 minutes. Maximum 3 reset attempts per hour per email to prevent abuse. User must enter old password OR verification code to reset. Email template should be simple, text-based, with clear expiry time. No password hints or security questions (security risk). Reset codes are 6-digit numbers, cryptographically random (not sequential)." \
  topic=authentication phase=requirements
```

**Why this is good:**
- Captures user requirements
- Includes security constraints
- Specifies timeouts and limits
- Documents UX expectations
- Notes what NOT to do and why

## Advanced Workflow Integration

### Session-Based Workflow

**Start of Day:**
```bash
# Review what you worked on last
scripts/mb query --limit 5

# Check stats to see coverage
scripts/mb stats

# Review decisions for today's area
scripts/mb query --topic <todays-topic> --phase decision
```

**During Implementation:**
```bash
# Before implementing a feature
scripts/mb query --topic <area> --phase decision
scripts/mb query --search "<relevant-keyword>"

# After making a decision
scripts/mb add -s "..." -c "..." topic=<area> phase=decision

# While implementing
scripts/mb add -s "..." -c "..." topic=<area> phase=backend-implementation

# When you hit a gotcha
scripts/mb add -s "..." -c "..." topic=<area> phase=troubleshooting
```

**End of Day:**
```bash
# Capture any final insights
scripts/mb add -s "..." -c "..." <tags>

# Review what you added today
scripts/mb query --all --limit 10

# Commit to git
git add .membase/
git commit -m "Document authentication decisions and implementation"
git push
```

### Team Collaboration Workflow

**Onboarding New Team Members:**
```bash
# Have them read high-level decisions
scripts/mb query --phase decision

# Review specific area they'll work on
scripts/mb query --topic <their-area>

# Show common gotchas
scripts/mb query --phase troubleshooting
```

**Code Review Integration:**
```bash
# Reviewer checks if decision is documented
scripts/mb query --topic <pr-area> --phase decision

# If new pattern, suggest documenting
scripts/mb add -s "..." -c "..." topic=<area> phase=backend-implementation
```

**Architecture Discussions:**
```bash
# Before architecture meeting, review existing decisions
scripts/mb query --phase decision

# During meeting, query related context
scripts/mb query --search "<topic>"

# After meeting, document decision
scripts/mb add -s "..." -c "..." phase=decision
```

## Git Integration

### How Membase Works with Git

Membase is designed to be git-friendly:

**File Format:**
- `memories.jsonl` uses one line per memory
- Each line is independent
- Sorted by UUID to spread changes across the file
- Git can auto-merge concurrent additions in most cases

**Schema Management:**
- `schema.json` is indented for readability
- Values are sorted alphabetically
- Independent changes merge cleanly

### Git Workflow

**After adding memories:**
```bash
git add .membase/
git commit -m "Document API rate limiting decision"
git push
```

**Receiving updates:**
```bash
git pull  # Automatically merges team's memories
```

**Handling conflicts:**

If you get a merge conflict in `memories.jsonl`:
1. Both changes are usually valid (just different memories)
2. Accept both changes
3. Re-run `scripts/mb query --all` to verify (file auto-sorts)

If you get a conflict in `schema.json`:
1. Merge dimension definitions (usually different dimensions)
2. Merge values (sort alphabetically)
3. Test with `scripts/mb dims`

### Branching Strategy

**Feature branches:**
```bash
# Create branch
git checkout -b feature/authentication

# Work and add memories
scripts/mb add -s "..." -c "..." topic=authentication phase=decision

# Commit
git add .membase/
git commit -m "Document JWT auth decision"

# Merge to main
git checkout main
git merge feature/authentication  # Memories come with the feature
```

**Why this works:**
- Decisions are tied to the code that implements them
- Team sees decisions when reviewing PRs
- Historical context preserved in git history

## Advanced Tagging Strategies

### Using Custom Dimensions

**Priority dimension for task management:**
```bash
scripts/mb dims add-dim priority "Task priority"
scripts/mb dims add priority critical
scripts/mb dims add priority high
scripts/mb dims add priority medium
scripts/mb dims add priority low

# Tag important items
scripts/mb add \
  -s "Security: SQL injection in search" \
  -c "..." \
  topic=api phase=troubleshooting priority=critical
```

**Status dimension for tracking:**
```bash
scripts/mb dims add-dim status "Implementation status"
scripts/mb dims add status planned
scripts/mb dims add status in-progress
scripts/mb dims add status completed
scripts/mb dims add status blocked

# Update as work progresses
scripts/mb edit abc123 status=in-progress
scripts/mb edit abc123 status=completed
```

**Component dimension for architecture:**
```bash
scripts/mb dims add-dim component "System component"
scripts/mb dims add component backend
scripts/mb dims add component frontend
scripts/mb dims add component database
scripts/mb dims add component cache
scripts/mb dims add component queue

# Tag by component
scripts/mb add -s "..." -c "..." component=cache topic=api phase=decision
```

### Multi-Dimensional Queries

Combine dimensions for precise queries:

```bash
# All critical troubleshooting items
scripts/mb query --phase troubleshooting priority=critical

# Completed database implementations
scripts/mb query --topic database phase=backend-implementation status=completed

# Frontend decisions
scripts/mb query component=frontend --phase decision
```

## Tips and Tricks

### Searching Effectively

**Use specific keywords:**
```bash
# Good: Specific technology names
scripts/mb query --search "PostgreSQL"
scripts/mb query --search "JWT"
scripts/mb query --search "Redis"

# Good: Specific file names
scripts/mb query --search "user.py"
scripts/mb query --search "ratelimit"
```

**Search is case-insensitive:**
```bash
scripts/mb query --search "jwt"      # Finds "JWT"
scripts/mb query --search "POSTGRES" # Finds "PostgreSQL"
```

**Combine search with filters:**
```bash
scripts/mb query --search "auth" --phase decision
scripts/mb query --search "error" --topic api
```

### Using ID Prefixes

You only need enough characters to be unique (usually 4-8):

```bash
# Brief listing shows first 8 characters
scripts/mb query --all
# Output: abc12345 [topic=auth phase=decision]

# Query with prefix
scripts/mb query --id abc1     # Usually enough
scripts/mb query --id abc12    # More specific
scripts/mb query --id abc12345 # Full 8 chars

# Edit with prefix
scripts/mb edit abc1 -s "New summary"

# Delete with prefix
scripts/mb delete abc1 -y
```

### Bulk Operations with JSON Output

**Export all memories:**
```bash
scripts/mb query --all --json > backup.json
```

**Filter and export:**
```bash
scripts/mb query --topic api --json > api-memories.json
scripts/mb query --phase decision --json > decisions.json
```

**Use with jq for processing:**
```bash
# Count memories by topic
scripts/mb query --all --json | jq -r '.[].tags.topic' | sort | uniq -c

# Extract all summaries
scripts/mb query --all --json | jq -r '.[].summary'

# Find memories without certain tag
scripts/mb query --all --json | jq '.[] | select(.tags.priority == null)'
```

### Maintaining Memory Hygiene

**Review and update regularly:**
```bash
# Review old decisions (might need updates)
scripts/mb query --phase decision

# Update if context changed
scripts/mb edit abc123 -c "Updated: Now using PostgreSQL 15 with..."

# Delete obsolete information
scripts/mb delete xyz789 -y
```

**Keep summaries concise:**
```bash
# Check summary length
scripts/mb query --all --json | jq -r '.[] | "\(.id[:8]) \(.summary | length) chars"'

# If too long, update
scripts/mb edit abc123 -s "Shorter, clearer summary"
```

**Tag consistently:**
```bash
# Review what tags you're using
scripts/mb stats

# Standardize on consistent values
# Good: "backend-implementation"
# Bad: "backend", "impl", "implementation"
```

### Scripting with Membase

**Check for existing decision before prompting:**
```bash
#!/bin/bash
topic="$1"
existing=$(scripts/mb query --topic "$topic" --phase decision --json | jq length)

if [ "$existing" -gt 0 ]; then
  echo "Found $existing existing decision(s) for $topic:"
  scripts/mb query --topic "$topic" --phase decision
else
  echo "No decisions found for $topic"
fi
```

**Auto-commit memories:**
```bash
#!/bin/bash
# commit-memories.sh
if [ -n "$(git status --porcelain .membase/)" ]; then
  git add .membase/
  git commit -m "Update project memories"
  echo "Committed memory changes"
else
  echo "No memory changes to commit"
fi
```

### Performance Notes

- Query operations are fast (in-memory filtering)
- File is read on each command (no persistent process)
- Suitable for hundreds to low thousands of memories
- For very large projects (>5000 memories), consider archiving old ones

### Troubleshooting

**Memory not found:**
```bash
# Make sure you're using enough of the ID
scripts/mb query --all | grep abc1

# Check if it was deleted
git log --all -- .membase/memories.jsonl | grep abc1
```

**Invalid dimension/value:**
```bash
# List available dimensions and values
scripts/mb dims

# Add missing value
scripts/mb dims add topic new-topic

# Create new dimension if needed
scripts/mb dims add-dim custom "Description"
```

**Schema validation errors:**
```bash
# Verify schema is valid JSON
python3 -m json.tool .membase/schema.json

# If corrupted, restore from git
git checkout .membase/schema.json
```

---

For essential usage, see [SKILL.md](SKILL.md).
