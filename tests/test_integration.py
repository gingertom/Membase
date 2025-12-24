"""
Integration tests for membase commands.
"""

import json
import os
from pathlib import Path

import pytest


class TestInitCommand:
    """Test 'mb init' command."""

    def test_init_creates_directory(self, temp_dir, mb_command):
        """Init should create .membase directory."""
        result = mb_command("init")

        assert result.returncode == 0
        assert "✓ Initialized membase" in result.stdout
        assert (temp_dir / ".membase").is_dir()

    def test_init_creates_schema(self, temp_dir, mb_command):
        """Init should create schema.json."""
        mb_command("init")

        schema_file = temp_dir / ".membase" / "schema.json"
        assert schema_file.exists()

        schema = json.loads(schema_file.read_text())
        assert "version" in schema
        assert "dimensions" in schema
        assert "values" in schema
        assert "topic" in schema["dimensions"]
        assert "phase" in schema["dimensions"]

    def test_init_creates_memories_file(self, temp_dir, mb_command):
        """Init should create empty memories.jsonl."""
        mb_command("init")

        memories_file = temp_dir / ".membase" / "memories.jsonl"
        assert memories_file.exists()
        assert memories_file.stat().st_size == 0

    def test_init_already_initialized(self, membase_init, mb_command):
        """Init should fail if already initialized."""
        result = mb_command("init", check=False)

        assert result.returncode == 1
        assert "already initialized" in result.stderr.lower()


class TestAddCommand:
    """Test 'mb add' command."""

    def test_add_valid_memory(self, membase_init, mb_command):
        """Adding valid memory should succeed."""
        mb_command("dims", "add", "topic", "test")

        result = mb_command(
            "add",
            "-s", "Test summary",
            "-c", "Test content",
            "topic=test", "phase=decision"
        )

        assert result.returncode == 0
        assert "✓ Added memory" in result.stdout

    def test_add_creates_memory_in_file(self, membase_init, mb_command):
        """Adding memory should write to memories.jsonl."""
        mb_command("dims", "add", "topic", "test")
        mb_command("add", "-s", "Test", "-c", "Content", "topic=test", "phase=decision")

        memories_file = membase_init / ".membase" / "memories.jsonl"
        content = memories_file.read_text()

        assert len(content) > 0
        memory = json.loads(content.strip())
        assert memory["summary"] == "Test"
        assert memory["content"] == "Content"
        assert memory["tags"] == {"topic": "test", "phase": "decision"}
        assert "id" in memory
        assert "created_at" in memory

    def test_add_missing_summary(self, membase_init, mb_command):
        """Adding without summary should fail."""
        result = mb_command("add", "-c", "Content", "phase=decision", check=False)

        assert result.returncode != 0

    def test_add_missing_content(self, membase_init, mb_command):
        """Adding without content should fail."""
        result = mb_command("add", "-s", "Summary", "phase=decision", check=False)

        assert result.returncode != 0

    def test_add_missing_tags(self, membase_init, mb_command):
        """Adding without tags should fail."""
        result = mb_command("add", "-s", "Summary", "-c", "Content", check=False)

        assert result.returncode != 0

    def test_add_empty_summary(self, membase_init, mb_command):
        """Adding with empty summary should fail."""
        result = mb_command("add", "-s", "", "-c", "Content", "phase=decision", check=False)

        assert result.returncode == 1
        assert "Summary" in result.stderr

    def test_add_empty_content(self, membase_init, mb_command):
        """Adding with empty content should fail."""
        mb_command("dims", "add", "topic", "test")
        result = mb_command("add", "-s", "Summary", "-c", "", "topic=test", check=False)

        assert result.returncode == 1
        assert "Content" in result.stderr

    def test_add_invalid_dimension(self, membase_init, mb_command):
        """Adding with invalid dimension should fail."""
        result = mb_command("add", "-s", "Test", "-c", "Content", "invalid=value", check=False)

        assert result.returncode == 1
        assert "Unknown dimension" in result.stderr

    def test_add_invalid_value(self, membase_init, mb_command):
        """Adding with invalid value should fail."""
        result = mb_command("add", "-s", "Test", "-c", "Content", "phase=invalid", check=False)

        assert result.returncode == 1
        assert "Unknown value" in result.stderr

    def test_add_typo_suggestion_dimension(self, membase_init, mb_command):
        """Typo in dimension should suggest correction."""
        result = mb_command("add", "-s", "Test", "-c", "Content", "topik=api", check=False)

        assert result.returncode == 1
        assert "Did you mean: topic" in result.stderr

    def test_add_typo_suggestion_value(self, membase_init, mb_command):
        """Typo in value should suggest correction."""
        result = mb_command("add", "-s", "Test", "-c", "Content", "phase=decission", check=False)

        assert result.returncode == 1
        assert "Did you mean: decision" in result.stderr


class TestQueryCommand:
    """Test 'mb query' command."""

    def test_query_all(self, populated_membase, mb_command):
        """Query --all should return all memories."""
        result = mb_command("query", "--all")

        assert result.returncode == 0
        # Should have 4 memories from populated_membase
        assert "4 memories" in result.stdout.lower() or "JWT auth" in result.stdout

    def test_query_by_topic(self, populated_membase, mb_command):
        """Query by topic should filter results."""
        result = mb_command("query", "--topic", "authentication")

        assert result.returncode == 0
        assert "JWT auth" in result.stdout
        assert "PostgreSQL" not in result.stdout  # Different topic

    def test_query_by_phase(self, populated_membase, mb_command):
        """Query by phase should filter results."""
        result = mb_command("query", "--phase", "decision")

        assert result.returncode == 0
        assert "JWT auth" in result.stdout
        assert "PostgreSQL" in result.stdout
        assert "User model" not in result.stdout  # Different phase

    def test_query_multiple_filters(self, populated_membase, mb_command):
        """Query with multiple filters should use AND logic."""
        result = mb_command("query", "--topic", "database", "--phase", "decision")

        assert result.returncode == 0
        assert "PostgreSQL" in result.stdout
        assert "JWT auth" not in result.stdout  # Different topic
        assert "User model" not in result.stdout  # Different phase

    def test_query_search(self, populated_membase, mb_command):
        """Query --search should do full-text search."""
        result = mb_command("query", "--search", "JWT")

        assert result.returncode == 0
        assert "JWT auth" in result.stdout
        assert "PostgreSQL" not in result.stdout

    def test_query_search_case_insensitive(self, populated_membase, mb_command):
        """Search should be case-insensitive."""
        result = mb_command("query", "--search", "jwt")

        assert result.returncode == 0
        assert "JWT auth" in result.stdout

    def test_query_by_id(self, populated_membase, mb_command):
        """Query by ID should return single memory."""
        # Get all memories to find an ID
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        mem_id = memories[0]["id"][:8]

        result = mb_command("query", "--id", mem_id)

        assert result.returncode == 0
        assert "Summary:" in result.stdout
        assert "Created:" in result.stdout

    def test_query_json_output(self, populated_membase, mb_command):
        """Query --json should output valid JSON."""
        result = mb_command("query", "--all", "--json")

        assert result.returncode == 0
        memories = json.loads(result.stdout)
        assert isinstance(memories, list)
        assert len(memories) == 4

    def test_query_no_results(self, populated_membase, mb_command):
        """Query with no matches should say so."""
        result = mb_command("query", "--search", "nonexistent")

        assert result.returncode == 0
        assert "No memories found" in result.stdout

    def test_query_adaptive_detail_few_results(self, membase_init, mb_command):
        """Query with ≤5 results should show full details."""
        mb_command("dims", "add", "topic", "test")
        mb_command("add", "-s", "Test 1", "-c", "Content 1", "topic=test", "phase=decision")

        result = mb_command("query", "--all")

        assert result.returncode == 0
        assert "Summary:" in result.stdout
        assert "Content 1" in result.stdout

    def test_query_adaptive_detail_many_results(self, membase_init, mb_command):
        """Query with >5 results should show brief summaries."""
        mb_command("dims", "add", "topic", "test")

        # Add 7 memories
        for i in range(7):
            mb_command("add", "-s", f"Test {i}", "-c", f"Content {i}", "topic=test", "phase=testing")

        result = mb_command("query", "--all")

        assert result.returncode == 0
        assert "Use --full for details" in result.stdout
        # Should not show full content
        assert "Summary:" not in result.stdout

    def test_query_force_full(self, membase_init, mb_command):
        """Query --full should force full details."""
        mb_command("dims", "add", "topic", "test")

        # Add 7 memories
        for i in range(7):
            mb_command("add", "-s", f"Test {i}", "-c", f"Content {i}", "topic=test", "phase=testing")

        result = mb_command("query", "--all", "--full")

        assert result.returncode == 0
        assert "Summary:" in result.stdout

    def test_query_force_brief(self, membase_init, mb_command):
        """Query --brief should force brief format."""
        mb_command("dims", "add", "topic", "test")
        mb_command("add", "-s", "Test", "-c", "Content", "topic=test", "phase=decision")

        result = mb_command("query", "--all", "--brief")

        assert result.returncode == 0
        assert "Use --full for details" in result.stdout
        assert "Summary:" not in result.stdout


class TestDimsCommand:
    """Test 'mb dims' command."""

    def test_dims_list(self, membase_init, mb_command):
        """Dims without arguments should list all dimensions."""
        result = mb_command("dims")

        assert result.returncode == 0
        assert "Dimensions:" in result.stdout
        assert "topic:" in result.stdout
        assert "phase:" in result.stdout

    def test_dims_add_value(self, membase_init, mb_command):
        """Dims add should add value to dimension."""
        result = mb_command("dims", "add", "topic", "authentication")

        assert result.returncode == 0
        assert "✓ Added value 'authentication' to dimension 'topic'" in result.stdout

        # Verify it's in schema
        result = mb_command("dims")
        assert "authentication" in result.stdout

    def test_dims_add_value_already_exists(self, membase_init, mb_command):
        """Adding existing value should fail."""
        mb_command("dims", "add", "topic", "test")
        result = mb_command("dims", "add", "topic", "test", check=False)

        assert result.returncode == 1
        assert "already exists" in result.stderr

    def test_dims_add_value_invalid_chars(self, membase_init, mb_command):
        """Adding value with invalid characters should fail."""
        result = mb_command("dims", "add", "topic", "Bad Name", check=False)

        assert result.returncode == 1
        assert "invalid" in result.stderr.lower()

    def test_dims_add_dim(self, membase_init, mb_command):
        """Dims add-dim should create new dimension."""
        result = mb_command("dims", "add-dim", "priority", "Task priority")

        assert result.returncode == 0
        assert "✓ Added dimension 'priority'" in result.stdout

        # Verify it's in schema
        result = mb_command("dims")
        assert "priority:" in result.stdout
        assert "Task priority" in result.stdout

    def test_dims_add_dim_already_exists(self, membase_init, mb_command):
        """Adding existing dimension should fail."""
        result = mb_command("dims", "add-dim", "topic", check=False)

        assert result.returncode == 1
        assert "already exists" in result.stderr

    def test_dims_add_dim_invalid_name(self, membase_init, mb_command):
        """Adding dimension with invalid name should fail."""
        result = mb_command("dims", "add-dim", "Bad Name", check=False)

        assert result.returncode == 1
        assert "invalid" in result.stderr.lower()


class TestEditCommand:
    """Test 'mb edit' command."""

    def test_edit_summary(self, populated_membase, mb_command):
        """Editing summary should work."""
        # Get a memory ID
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        mem_id = memories[0]["id"][:8]

        result = mb_command("edit", mem_id, "-s", "New summary")

        assert result.returncode == 0
        assert "✓ Updated memory" in result.stdout

        # Verify change
        result = mb_command("query", "--id", mem_id)
        assert "New summary" in result.stdout

    def test_edit_content(self, populated_membase, mb_command):
        """Editing content should work."""
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        mem_id = memories[0]["id"][:8]

        result = mb_command("edit", mem_id, "-c", "New content")

        assert result.returncode == 0
        assert "✓ Updated memory" in result.stdout

        # Verify change
        result = mb_command("query", "--id", mem_id)
        assert "New content" in result.stdout

    def test_edit_tags(self, populated_membase, mb_command):
        """Editing tags should work."""
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        mem_id = memories[0]["id"][:8]

        # Change phase
        result = mb_command("edit", mem_id, "phase=planning")

        assert result.returncode == 0

        # Verify change
        result = mb_command("query", "--id", mem_id)
        assert "phase=planning" in result.stdout

    def test_edit_no_changes(self, populated_membase, mb_command):
        """Editing without changes should say so."""
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        mem_id = memories[0]["id"][:8]

        result = mb_command("edit", mem_id)

        assert result.returncode == 0
        assert "No changes made" in result.stdout

    def test_edit_sets_updated_at(self, populated_membase, mb_command):
        """Editing should set updated_at timestamp."""
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        mem_id = memories[0]["id"]
        mem_id_short = mem_id[:8]

        # Edit the memory
        mb_command("edit", mem_id_short, "-s", "Updated")

        # Check JSON output - query all and find the memory
        result = mb_command("query", "--all", "--json")
        all_memories = json.loads(result.stdout)
        memory = next(m for m in all_memories if m["id"] == mem_id)

        assert "updated_at" in memory

    def test_edit_not_found(self, membase_init, mb_command):
        """Editing non-existent memory should fail."""
        result = mb_command("edit", "nonexistent", "-s", "Test", check=False)

        assert result.returncode == 1
        assert "not found" in result.stderr


class TestDeleteCommand:
    """Test 'mb delete' command."""

    def test_delete_with_yes_flag(self, populated_membase, mb_command):
        """Delete with -y should work without prompt."""
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        initial_count = len(memories)
        mem_id = memories[0]["id"][:8]

        result = mb_command("delete", mem_id, "-y")

        assert result.returncode == 0
        assert "✓ Deleted memory" in result.stdout

        # Verify deletion
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        assert len(memories) == initial_count - 1

    def test_delete_not_found(self, membase_init, mb_command):
        """Deleting non-existent memory should fail."""
        result = mb_command("delete", "nonexistent", "-y", check=False)

        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_delete_removes_from_file(self, populated_membase, mb_command):
        """Deleting should remove memory from file."""
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        mem_id = memories[0]["id"]

        mb_command("delete", mem_id[:8], "-y")

        # Read file directly
        memories_file = populated_membase / ".membase" / "memories.jsonl"
        content = memories_file.read_text()

        assert mem_id not in content


class TestStatsCommand:
    """Test 'mb stats' command."""

    def test_stats_shows_total(self, populated_membase, mb_command):
        """Stats should show total memory count."""
        result = mb_command("stats")

        assert result.returncode == 0
        assert "Total memories: 4" in result.stdout

    def test_stats_shows_breakdown(self, populated_membase, mb_command):
        """Stats should show breakdown by dimension."""
        result = mb_command("stats")

        assert result.returncode == 0
        assert "phase:" in result.stdout
        assert "topic:" in result.stdout
        assert "decision:" in result.stdout
        assert "backend-implementation:" in result.stdout

    def test_stats_empty_membase(self, membase_init, mb_command):
        """Stats on empty membase should show zero."""
        result = mb_command("stats")

        assert result.returncode == 0
        assert "Total memories: 0" in result.stdout


class TestVersionFlag:
    """Test --version flag."""

    def test_version_flag(self, temp_dir, mb_command):
        """--version should show version."""
        result = mb_command("--version")

        assert result.returncode == 0
        assert "membase" in result.stdout.lower()
        assert "1.0.0" in result.stdout


class TestCLIErrors:
    """Test CLI error handling."""

    def test_no_command(self, temp_dir, mb_command):
        """No command should show help."""
        result = mb_command(check=False)

        assert result.returncode == 1

    def test_command_before_init(self, temp_dir, mb_command):
        """Commands before init should fail."""
        result = mb_command("add", "-s", "Test", "-c", "Content", "phase=decision", check=False)

        assert result.returncode == 1
        assert "not a membase project" in result.stderr.lower()
