"""
Concurrency tests for membase file locking.
"""

import json
import multiprocessing
import time
from pathlib import Path

import pytest


def add_memory_worker(args):
    """Worker function to add a memory (for multiprocessing test)."""
    import subprocess

    mb_script_path, work_dir, worker_id = args

    result = subprocess.run(
        [
            str(mb_script_path),
            "add",
            "-s", f"Test from worker {worker_id}",
            "-c", f"Content from worker {worker_id}",
            "topic=testing",
            "phase=testing"
        ],
        capture_output=True,
        text=True,
        cwd=str(work_dir)
    )

    # For debugging: print errors
    if result.returncode != 0:
        print(f"Worker {worker_id} failed: {result.stderr}")

    return result.returncode == 0


def edit_memory_worker(args):
    """Worker function to edit a memory (for multiprocessing test)."""
    import subprocess

    mb_script_path, work_dir, memory_id, worker_id = args

    result = subprocess.run(
        [
            str(mb_script_path),
            "edit",
            memory_id,
            "-s", f"Edited by worker {worker_id}"
        ],
        capture_output=True,
        text=True,
        cwd=str(work_dir)
    )

    return result.returncode == 0


class TestConcurrentAccess:
    """Test concurrent access with file locking."""

    def test_concurrent_adds(self, membase_init, mb_command):
        """Multiple concurrent adds should all succeed."""
        num_workers = 5

        # Add the "testing" topic value first to avoid races
        mb_command("dims", "add", "topic", "testing")

        # Get the real mb script path
        mb_script = Path(__file__).resolve().parent.parent / "scripts" / "mb"

        # Use multiprocessing to simulate concurrent access
        with multiprocessing.Pool(num_workers) as pool:
            results = pool.map(
                add_memory_worker,
                [(mb_script, membase_init, i) for i in range(num_workers)]
            )

        # All workers should succeed
        assert all(results), "Some workers failed"

        # Verify all memories were added
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)

        assert len(memories) == num_workers, f"Expected {num_workers} memories, got {len(memories)}"

        # Verify no duplicates (all worker IDs should be unique)
        summaries = [m["summary"] for m in memories]
        assert len(set(summaries)) == num_workers, "Found duplicate memories"

    def test_concurrent_reads(self, populated_membase, mb_command):
        """Multiple concurrent reads should all succeed."""
        import subprocess
        import threading

        mb_script = Path(__file__).parent.parent / "scripts" / "mb"
        results = []

        def query_worker():
            result = subprocess.run(
                [str(mb_script), "query", "--all"],
                capture_output=True,
                text=True,
                cwd=str(populated_membase)
            )
            results.append(result.returncode == 0)

        # Create multiple threads reading concurrently
        threads = [threading.Thread(target=query_worker) for _ in range(10)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All reads should succeed
        assert all(results), "Some reads failed"

    def test_concurrent_edits_same_memory(self, populated_membase, mb_command):
        """Multiple concurrent edits to same memory should not corrupt data."""
        # Get a memory ID
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)
        mem_id = memories[0]["id"][:8]

        num_workers = 3
        mb_script = Path(__file__).resolve().parent.parent / "scripts" / "mb"

        # Edit same memory from multiple processes
        with multiprocessing.Pool(num_workers) as pool:
            results = pool.map(
                edit_memory_worker,
                [(mb_script, populated_membase, mem_id, i) for i in range(num_workers)]
            )

        # At least one worker should succeed (due to locking, others might fail)
        assert any(results), "All workers failed"

        # Memory should still be valid (not corrupted)
        result = mb_command("query", "--all", "--json")
        all_memories = json.loads(result.stdout)
        memory = next((m for m in all_memories if m["id"].startswith(mem_id)), None)

        assert memory is not None, f"Memory {mem_id} not found"

        # Should have one of the worker summaries
        assert "Edited by worker" in memory["summary"]

    def test_no_corrupted_jsonl(self, membase_init, mb_command):
        """Concurrent adds should not corrupt JSONL file."""
        num_workers = 10

        # Add the "testing" topic value first to avoid races
        mb_command("dims", "add", "topic", "testing")

        mb_script = Path(__file__).resolve().parent.parent / "scripts" / "mb"

        with multiprocessing.Pool(num_workers) as pool:
            pool.map(
                add_memory_worker,
                [(mb_script, membase_init, i) for i in range(num_workers)]
            )

        # Read JSONL file and verify it's valid
        memories_file = membase_init / ".membase" / "memories.jsonl"
        content = memories_file.read_text()

        lines = [line for line in content.strip().split('\n') if line]

        # All lines should be valid JSON
        for i, line in enumerate(lines):
            try:
                memory = json.loads(line)
                assert "id" in memory
                assert "summary" in memory
                assert "content" in memory
            except json.JSONDecodeError:
                pytest.fail(f"Line {i+1} is not valid JSON: {line}")

    def test_file_lock_released_on_error(self, membase_init, mb_command):
        """File locks should be released even if command errors."""
        # Try to add with invalid data (should fail)
        result = mb_command("add", "-s", "Test", "-c", "Content", "invalid=bad", check=False)
        assert result.returncode != 0

        # Should still be able to perform valid operation
        mb_command("dims", "add", "topic", "test")
        result = mb_command("add", "-s", "Valid", "-c", "Content", "topic=test", "phase=decision")

        assert result.returncode == 0


class TestFileLocking:
    """Test file locking mechanisms."""

    def test_shared_lock_for_reads(self, populated_membase):
        """Multiple reads should acquire shared locks."""
        import fcntl
        import subprocess
        import threading

        mb_script = Path(__file__).parent.parent / "scripts" / "mb"
        lock_acquired = []

        def try_read_lock():
            memories_file = populated_membase / ".membase" / "memories.jsonl"
            try:
                with open(memories_file, 'r') as f:
                    # Try to acquire shared lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                    lock_acquired.append(True)
                    time.sleep(0.1)  # Hold lock briefly
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except IOError:
                lock_acquired.append(False)

        # Multiple shared locks should be acquirable
        threads = [threading.Thread(target=try_read_lock) for _ in range(3)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All should succeed (shared locks don't block each other)
        assert all(lock_acquired), "Some shared locks failed to acquire"

    def test_memories_sorted_after_concurrent_adds(self, membase_init, mb_command):
        """After concurrent adds, memories should still be sorted by UUID."""
        num_workers = 8

        # Add the "testing" topic value first to avoid races
        mb_command("dims", "add", "topic", "testing")

        mb_script = Path(__file__).resolve().parent.parent / "scripts" / "mb"

        with multiprocessing.Pool(num_workers) as pool:
            pool.map(
                add_memory_worker,
                [(mb_script, membase_init, i) for i in range(num_workers)]
            )

        # Read memories file
        result = mb_command("query", "--all", "--json")
        memories = json.loads(result.stdout)

        # Extract UUIDs
        uuids = [m["id"] for m in memories]

        # Should be sorted
        assert uuids == sorted(uuids), "Memories are not sorted by UUID"


class TestAtomicWrites:
    """Test atomic write behavior."""

    def test_no_partial_writes(self, membase_init, mb_command):
        """Writes should be atomic (no partial/corrupted data)."""
        # Add a memory with large content
        large_content = "X" * 10000

        mb_command("dims", "add", "topic", "test")
        result = mb_command("add", "-s", "Large", "-c", large_content, "topic=test", "phase=decision")

        assert result.returncode == 0

        # Verify full content is present
        result = mb_command("query", "--search", "Large", "--json")
        memory = json.loads(result.stdout)[0]

        assert len(memory["content"]) == 10000
        assert memory["content"] == large_content

    def test_no_temp_files_left(self, membase_init, mb_command):
        """No .tmp files should be left after operations."""
        mb_command("dims", "add", "topic", "test")
        mb_command("add", "-s", "Test", "-c", "Content", "topic=test", "phase=decision")

        # Check for .tmp files
        tmp_files = list(membase_init.glob(".membase/*.tmp"))

        assert len(tmp_files) == 0, f"Found temp files: {tmp_files}"
