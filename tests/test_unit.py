"""
Unit tests for membase helper functions.
"""

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

# Import the mb module
# We need to import mb as a module, but it doesn't have .py extension
# Use a namespace and exec() to load it
mb_path = Path(__file__).resolve().parent.parent / "scripts" / "mb"

if not mb_path.exists():
    raise FileNotFoundError(f"mb script not found at {mb_path}")

# Create a module namespace and execute the script
import types
mb = types.ModuleType("mb")
mb.__file__ = str(mb_path)

with open(mb_path, 'r') as f:
    code = compile(f.read(), str(mb_path), 'exec')
    exec(code, mb.__dict__)


class TestValidation:
    """Test validation functions."""

    def test_validate_summary_valid(self):
        """Valid summaries should pass."""
        mb.validate_summary("This is a valid summary")
        mb.validate_summary("A" * 100)  # Max length

    def test_validate_summary_empty(self):
        """Empty summaries should fail."""
        with pytest.raises(SystemExit):
            mb.validate_summary("")

    def test_validate_summary_whitespace_only(self):
        """Whitespace-only summaries should fail."""
        with pytest.raises(SystemExit):
            mb.validate_summary("   ")

    def test_validate_summary_too_long(self):
        """Summaries over 100 chars should fail."""
        with pytest.raises(SystemExit):
            mb.validate_summary("A" * 101)

    def test_validate_content_valid(self):
        """Valid content should pass."""
        mb.validate_content("This is valid content")
        mb.validate_content("X" * 1000)  # Long but under limit

    def test_validate_content_empty(self):
        """Empty content should fail."""
        with pytest.raises(SystemExit):
            mb.validate_content("")

    def test_validate_content_whitespace_only(self):
        """Whitespace-only content should fail."""
        with pytest.raises(SystemExit):
            mb.validate_content("   \n\t  ")

    def test_validate_content_too_long(self):
        """Content over 1MB should fail."""
        with pytest.raises(SystemExit):
            mb.validate_content("X" * (mb.MAX_CONTENT_LENGTH + 1))

    def test_validate_identifier_valid(self):
        """Valid identifiers should pass."""
        mb.validate_identifier("topic", 50, "Test field")
        mb.validate_identifier("backend-implementation", 50, "Test field")
        mb.validate_identifier("api123", 50, "Test field")

    def test_validate_identifier_empty(self):
        """Empty identifiers should fail."""
        with pytest.raises(SystemExit):
            mb.validate_identifier("", 50, "Test field")

    def test_validate_identifier_whitespace(self):
        """Whitespace-only identifiers should fail."""
        with pytest.raises(SystemExit):
            mb.validate_identifier("   ", 50, "Test field")

    def test_validate_identifier_invalid_chars(self):
        """Identifiers with invalid chars should fail."""
        with pytest.raises(SystemExit):
            mb.validate_identifier("Bad Name", 50, "Test field")

        with pytest.raises(SystemExit):
            mb.validate_identifier("UPPERCASE", 50, "Test field")

        with pytest.raises(SystemExit):
            mb.validate_identifier("under_score", 50, "Test field")

    def test_validate_identifier_too_long(self):
        """Identifiers over max length should fail."""
        with pytest.raises(SystemExit):
            mb.validate_identifier("a" * 51, 50, "Test field")

    def test_validate_tags_valid(self):
        """Valid tags should pass."""
        schema = mb.DEFAULT_SCHEMA
        tags = {"topic": "database", "phase": "decision"}
        # This will fail because topic=database doesn't exist in default schema
        # We need to add it first
        schema["values"]["topic"] = ["database"]
        mb.validate_tags(tags, schema)

    def test_validate_tags_empty(self):
        """Empty tags should fail."""
        schema = mb.DEFAULT_SCHEMA
        with pytest.raises(SystemExit):
            mb.validate_tags({}, schema)

    def test_validate_tags_unknown_dimension(self):
        """Unknown dimensions should fail with suggestion."""
        schema = mb.DEFAULT_SCHEMA
        tags = {"topik": "value"}  # Typo
        with pytest.raises(SystemExit):
            mb.validate_tags(tags, schema)

    def test_validate_tags_unknown_value(self):
        """Unknown values should fail with suggestion."""
        schema = mb.DEFAULT_SCHEMA
        schema["values"]["topic"] = ["database"]
        tags = {"topic": "databse"}  # Typo
        with pytest.raises(SystemExit):
            mb.validate_tags(tags, schema)


class TestMemoryStructureValidation:
    """Test memory data structure validation."""

    def test_validate_memory_structure_valid(self):
        """Valid memory structure should pass."""
        memory = {
            "id": str(uuid.uuid4()),
            "summary": "Test summary",
            "content": "Test content",
            "tags": {"phase": "decision"},
            "created_at": "2025-01-01T00:00:00+00:00"
        }
        mb.validate_memory_structure(memory, 1)

    def test_validate_memory_structure_not_dict(self):
        """Non-dict memory should fail."""
        with pytest.raises(SystemExit):
            mb.validate_memory_structure([], 1)

        with pytest.raises(SystemExit):
            mb.validate_memory_structure("string", 1)

    def test_validate_memory_structure_missing_fields(self):
        """Memory missing required fields should fail."""
        memory = {"id": str(uuid.uuid4())}
        with pytest.raises(SystemExit):
            mb.validate_memory_structure(memory, 1)

    def test_validate_memory_structure_invalid_uuid(self):
        """Memory with invalid UUID should fail."""
        memory = {
            "id": "not-a-uuid",
            "summary": "Test",
            "content": "Test",
            "tags": {},
            "created_at": "2025-01-01T00:00:00+00:00"
        }
        with pytest.raises(SystemExit):
            mb.validate_memory_structure(memory, 1)

    def test_validate_memory_structure_invalid_tags_type(self):
        """Memory with non-dict tags should fail."""
        memory = {
            "id": str(uuid.uuid4()),
            "summary": "Test",
            "content": "Test",
            "tags": [],  # Should be dict
            "created_at": "2025-01-01T00:00:00+00:00"
        }
        with pytest.raises(SystemExit):
            mb.validate_memory_structure(memory, 1)


class TestParseTagArgs:
    """Test tag argument parsing."""

    def test_parse_tag_args_valid(self):
        """Valid tag arguments should parse correctly."""
        args = ["topic=api", "phase=decision"]
        result = mb.parse_tag_args(args)
        assert result == {"topic": "api", "phase": "decision"}

    def test_parse_tag_args_with_equals_in_value(self):
        """Tag values with equals signs should work."""
        args = ["topic=api", "note=foo=bar"]
        result = mb.parse_tag_args(args)
        assert result == {"topic": "api", "note": "foo=bar"}

    def test_parse_tag_args_invalid_format(self):
        """Invalid tag format should fail."""
        args = ["topic"]  # Missing =value
        with pytest.raises(SystemExit):
            mb.parse_tag_args(args)


class TestFindMemoryByIdPrefix:
    """Test memory ID prefix matching."""

    def test_find_memory_by_id_prefix_exact(self):
        """Exact ID match should work."""
        mem_id = str(uuid.uuid4())
        memories = [
            {"id": mem_id, "summary": "Test"},
            {"id": str(uuid.uuid4()), "summary": "Other"}
        ]
        result = mb.find_memory_by_id_prefix(memories, mem_id)
        assert result["id"] == mem_id

    def test_find_memory_by_id_prefix_short(self):
        """Short prefix match should work."""
        mem_id = "abc12345-1234-1234-1234-123456789012"
        memories = [
            {"id": mem_id, "summary": "Test"},
            {"id": "def12345-1234-1234-1234-123456789012", "summary": "Other"}
        ]
        result = mb.find_memory_by_id_prefix(memories, "abc")
        assert result["id"] == mem_id

    def test_find_memory_by_id_prefix_not_found(self):
        """Non-existent prefix should fail."""
        memories = [{"id": str(uuid.uuid4()), "summary": "Test"}]
        with pytest.raises(SystemExit):
            mb.find_memory_by_id_prefix(memories, "xyz")

    def test_find_memory_by_id_prefix_ambiguous(self):
        """Ambiguous prefix should fail."""
        memories = [
            {"id": "abc12345-1234-1234-1234-123456789012", "summary": "Test 1"},
            {"id": "abc67890-1234-1234-1234-123456789012", "summary": "Test 2"}
        ]
        with pytest.raises(SystemExit):
            mb.find_memory_by_id_prefix(memories, "abc")


class TestAtomicWrite:
    """Test atomic write functionality."""

    def test_atomic_write_creates_file(self, temp_dir):
        """Atomic write should create file successfully."""
        test_file = temp_dir / "test.txt"
        content = "Test content\n"

        mb.atomic_write(test_file, content)

        assert test_file.exists()
        assert test_file.read_text() == content

    def test_atomic_write_overwrites_existing(self, temp_dir):
        """Atomic write should overwrite existing file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Old content")

        new_content = "New content\n"
        mb.atomic_write(test_file, new_content)

        assert test_file.read_text() == new_content

    def test_atomic_write_no_temp_file_left(self, temp_dir):
        """Atomic write should not leave temp file."""
        test_file = temp_dir / "test.txt"
        mb.atomic_write(test_file, "Content")

        temp_files = list(temp_dir.glob("*.tmp"))
        assert len(temp_files) == 0


class TestSchemaVersioning:
    """Test schema versioning."""

    def test_default_schema_has_version(self):
        """Default schema should have version field."""
        assert "version" in mb.DEFAULT_SCHEMA
        assert mb.DEFAULT_SCHEMA["version"] == 1

    def test_load_schema_migrates_old_version(self, temp_dir):
        """Loading old schema should add version field."""
        membase_dir = temp_dir / ".membase"
        membase_dir.mkdir()
        schema_file = membase_dir / "schema.json"

        # Create old schema without version
        old_schema = {
            "dimensions": {"topic": "Topics"},
            "values": {"topic": []}
        }
        schema_file.write_text(json.dumps(old_schema))

        # Change to temp dir so get_membase_paths works
        os.chdir(temp_dir)

        schema = mb.load_schema()
        assert "version" in schema
        assert schema["version"] == 1
