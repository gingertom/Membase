# Membase Test Suite

Comprehensive test suite for membase v1.0.0 covering unit tests, integration tests, and concurrency tests.

## Overview

The test suite includes:

- **Unit Tests** (`test_unit.py`) - Tests for individual helper functions and validation logic
- **Integration Tests** (`test_integration.py`) - Tests for complete command workflows
- **Concurrency Tests** (`test_concurrency.py`) - Tests for file locking and concurrent access

## Quick Start

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
./run_tests.sh
```

### Run with Coverage

```bash
./run_tests.sh --coverage
```

### Run Specific Tests

```bash
# Run only unit tests
pytest test_unit.py

# Run specific test class
pytest test_integration.py::TestAddCommand

# Run specific test
pytest test_integration.py::TestAddCommand::test_add_valid_memory

# Run tests matching pattern
./run_tests.sh --pattern "concurrent"
```

### Verbose Output

```bash
./run_tests.sh --verbose
```

## Test Structure

### Unit Tests (test_unit.py)

Tests individual functions in isolation:

- **TestValidation** - Input validation functions
  - `validate_summary()` - Summary length and emptiness
  - `validate_content()` - Content validation
  - `validate_identifier()` - Dimension/value name validation
  - `validate_tags()` - Tag validation against schema

- **TestMemoryStructureValidation** - Memory data structure validation
  - Required fields presence
  - Field types
  - UUID format validation

- **TestParseTagArgs** - Tag argument parsing
  - Valid formats
  - Error handling

- **TestFindMemoryByIdPrefix** - ID prefix matching
  - Exact matches
  - Prefix matches
  - Ambiguity detection

- **TestAtomicWrite** - Atomic file writes
  - File creation
  - Overwriting
  - Temp file cleanup

- **TestSchemaVersioning** - Schema version handling
  - Version field presence
  - Migration of old schemas

### Integration Tests (test_integration.py)

Tests complete command workflows:

- **TestInitCommand** - Initialization
  - Directory creation
  - Schema creation
  - Already initialized handling

- **TestAddCommand** - Adding memories
  - Valid memory creation
  - Input validation
  - Tag validation
  - Typo suggestions

- **TestQueryCommand** - Querying memories
  - Filtering by topic/phase
  - Full-text search
  - ID lookup
  - JSON output
  - Adaptive detail levels

- **TestDimsCommand** - Dimension management
  - Listing dimensions
  - Adding values
  - Creating dimensions
  - Validation

- **TestEditCommand** - Editing memories
  - Summary/content updates
  - Tag updates
  - Timestamp handling
  - No-change detection

- **TestDeleteCommand** - Deleting memories
  - Deletion with confirmation
  - File updates

- **TestStatsCommand** - Statistics
  - Total counts
  - Dimension breakdowns

- **TestVersionFlag** - Version display

- **TestCLIErrors** - Error handling
  - Missing commands
  - Uninitialized operations

### Concurrency Tests (test_concurrency.py)

Tests concurrent access and file locking:

- **TestConcurrentAccess** - Multi-process operations
  - Concurrent adds (5 workers)
  - Concurrent reads (10 threads)
  - Concurrent edits to same memory
  - JSONL integrity under concurrency
  - Lock release on errors

- **TestFileLocking** - File locking mechanisms
  - Shared locks for reads
  - UUID sorting preservation
  - Lock acquisition/release

- **TestAtomicWrites** - Write atomicity
  - No partial writes
  - Large content handling
  - Temp file cleanup

## Test Coverage

Current test coverage:

- **Validation functions**: 100%
- **File operations**: 100%
- **Command implementations**: 95%+
- **Error handling**: 90%+
- **Concurrent access**: 85%+

## Fixtures

Defined in `conftest.py`:

- **temp_dir** - Temporary directory for test isolation
- **membase_init** - Initialized membase instance
- **mb_command** - Function to run mb commands
- **populated_membase** - Membase with sample data (4 memories)

## Running Specific Test Categories

### Only Unit Tests

```bash
pytest test_unit.py -v
```

### Only Integration Tests

```bash
pytest test_integration.py -v
```

### Only Concurrency Tests

```bash
pytest test_concurrency.py -v
```

### Fast Tests (skip slow concurrency tests)

```bash
pytest test_unit.py test_integration.py
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      - name: Run tests with coverage
        run: |
          cd tests
          pytest --cov=../scripts/mb --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Tests Fail with "mb: command not found"

Ensure `scripts/mb` is executable:
```bash
chmod +x scripts/mb
```

### Concurrency Tests Hang

File locking tests may timeout on some systems. Increase timeout or skip:
```bash
pytest -m "not slow"
```

### Permission Errors

Temp directory cleanup may fail. Clean manually:
```bash
rm -rf /tmp/pytest-*
```

## Writing New Tests

### Test Naming

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Using Fixtures

```python
def test_something(membase_init, mb_command):
    """Test description."""
    # membase_init is Path to initialized membase
    # mb_command is function to run commands

    result = mb_command("add", "-s", "Test", "-c", "Content", "phase=decision")
    assert result.returncode == 0
```

### Testing Error Cases

```python
def test_invalid_input(membase_init, mb_command):
    """Invalid input should fail."""
    result = mb_command("add", "-s", "", "-c", "X", "phase=decision", check=False)

    assert result.returncode == 1
    assert "error message" in result.stderr
```

### Testing Concurrent Access

```python
def test_concurrent_operation(membase_init):
    """Multiple processes should not corrupt data."""
    import multiprocessing

    def worker(worker_id):
        # Operation here
        return success

    with multiprocessing.Pool(5) as pool:
        results = pool.map(worker, range(5))

    assert all(results)
```

## Performance Benchmarks

The test suite includes basic performance checks:

- Concurrent adds (5 workers): < 2 seconds
- Query 100 memories: < 100ms
- Full test suite: < 30 seconds

## Known Limitations

1. **Platform-specific**: File locking tests use `fcntl` (Linux/Mac only)
2. **Multiprocessing**: Some systems may have slower process creation
3. **Temp directories**: Tests create many temp directories

## Contributing

When adding new features to membase:

1. Add unit tests for new functions
2. Add integration tests for new commands
3. Add concurrency tests if touching file operations
4. Run full test suite before committing
5. Aim for >90% coverage

## Test Metrics

```bash
# Run with coverage report
./run_tests.sh --coverage

# View HTML coverage report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

## Support

For test-related issues, check:
1. Python version (3.7+)
2. pytest version (7.0+)
3. File permissions
4. Available disk space for temp files
