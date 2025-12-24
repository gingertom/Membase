"""
Pytest configuration and shared fixtures for membase tests.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path so we can import the mb module
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test isolation."""
    tmpdir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(tmpdir)
    yield Path(tmpdir)
    os.chdir(original_cwd)
    shutil.rmtree(tmpdir)


@pytest.fixture
def membase_init(temp_dir):
    """Initialize a membase instance in temp directory."""
    from subprocess import run, PIPE

    mb_script = Path(__file__).parent.parent / "scripts" / "mb"
    result = run([str(mb_script), "init"], capture_output=True, text=True)

    assert result.returncode == 0
    assert (temp_dir / ".membase").exists()
    assert (temp_dir / ".membase" / "schema.json").exists()
    assert (temp_dir / ".membase" / "memories.jsonl").exists()

    return temp_dir


@pytest.fixture
def mb_command(temp_dir):
    """Return a function to run mb commands."""
    from subprocess import run, PIPE

    mb_script = Path(__file__).parent.parent / "scripts" / "mb"

    def run_mb(*args, input_text=None, check=True):
        """Run mb command with arguments."""
        cmd = [str(mb_script)] + list(args)
        result = run(
            cmd,
            capture_output=True,
            text=True,
            input=input_text,
            cwd=str(temp_dir)
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
        return result

    return run_mb


@pytest.fixture
def populated_membase(membase_init, mb_command):
    """Create a membase with some test data."""
    # Add topics
    mb_command("dims", "add", "topic", "authentication")
    mb_command("dims", "add", "topic", "database")
    mb_command("dims", "add", "topic", "api")

    # Add some memories
    memories = [
        {
            "summary": "JWT auth with 24h expiry",
            "content": "Using JWT for stateless authentication. Access tokens expire in 24h.",
            "tags": ["topic=authentication", "phase=decision"]
        },
        {
            "summary": "PostgreSQL for main database",
            "content": "Chose PostgreSQL over MySQL for better JSON support and PostGIS.",
            "tags": ["topic=database", "phase=decision"]
        },
        {
            "summary": "User model in src/models/user.py",
            "content": "User model includes: username, email, password_hash, created_at, updated_at.",
            "tags": ["topic=database", "phase=backend-implementation"]
        },
        {
            "summary": "API rate limiting with Redis",
            "content": "Implemented sliding window rate limiting. 100 requests per 60 seconds.",
            "tags": ["topic=api", "phase=backend-implementation"]
        },
    ]

    for mem in memories:
        mb_command(
            "add",
            "-s", mem["summary"],
            "-c", mem["content"],
            *mem["tags"]
        )

    return membase_init
