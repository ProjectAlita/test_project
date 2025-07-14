# Arbiter Test Documentation

This document explains the test suite for the Arbiter distributed task queue system, how to run the tests, and what each test verifies.

## Test Environment

The test suite uses a mock event node and in-memory task execution to test Arbiter functionality without requiring external dependencies like Redis. This makes the tests fast and self-contained.

## Running Tests

To run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_arbiter.py

# Run specific test
pytest tests/test_arbiter.py::TestArbiter::test_pipe
```

## Test Setup

The test environment is set up using pytest fixtures that:

1. Create a MockEventNode for event communication
2. Start a test Minion with predefined task functions
3. Tear down all components after tests complete

## Test Minion

The test Minion (`tests/minion.py`) provides several task functions for testing:

- `simple_add`: Adds two numbers
- `add`: Adds two numbers and initiates another task
- `add_in_pipe`: Adds two numbers and a previous result (for pipeline testing)
- `long_running`: Sleeps for 180 seconds (for testing task termination)

The Minion is configured to use threading (rather than multiprocessing) and memory transport for test efficiency.

## Test Cases

### test_task_in_task

Verifies that tasks can initiate other tasks and that results are properly returned and tracked.

1. Creates multiple "simple_add" tasks
2. Verifies tasks progress through their lifecycle states
3. Confirms correct results (1 + 2 = 3)
4. Checks that worker resources are properly released after completion

### test_squad

Tests the "squad" pattern (group of concurrent tasks).

1. Creates a squad of "simple_add" tasks
2. Waits for all tasks to complete
3. Verifies that task count and completion status match expectations
4. Ensures worker resources are properly released

### test_pipe

Tests the "pipe" pattern (sequential task chain).

1. Creates a pipeline of 20 "add_in_pipe" tasks
2. Verifies that results are passed correctly between tasks
3. Confirms increasing result values (4, 8, 12, etc.)
4. Ensures all tasks complete and resources are released

### test_kill_task

Validates task termination functionality.

1. Starts a long-running task (180 seconds)
2. Kills the task after 2 seconds
3. Verifies the task is stopped before its natural completion
4. Ensures worker resources are properly released

### test_kill_group

Tests termination of an entire task group.

1. Creates a squad of long-running tasks
2. Kills the entire group after 5 seconds
3. Verifies all tasks are stopped before natural completion
4. Ensures worker resources are properly released

### test_squad_callback

Tests the callback functionality for task groups.

1. Creates a task squad with a callback
2. Verifies that the callback executes after all tasks complete
3. Confirms the callback result is correct (5 + 4 = 9)
4. Ensures worker resources are properly released

### test_squad_finalyzer

Tests the finalizer functionality for task groups.

1. Creates a task squad with both a callback and finalizer
2. Verifies that both execute after all tasks complete
3. Confirms the finalizer runs last and produces correct results
4. Ensures worker resources are properly released

### test_sync_task

Validates synchronous task execution.

1. Executes a "simple_add" task synchronously
2. Verifies the task completes with correct results
3. Ensures worker resources are properly released

## Test Coverage

The test suite covers the following aspects of Arbiter functionality:

- Basic task execution and result retrieval
- Task lifecycle states (initiated, running, done)
- Task group execution (squad pattern)
- Sequential task execution (pipe pattern)
- Task termination (individual and group)
- Callback and finalizer functionality
- Synchronous vs. asynchronous execution
- Worker resource management
- Task-initiated subtasks

## Mocking Strategy

The test suite uses `MockEventNode` to simulate the event communication layer typically provided by Redis or other backends. This allows testing the core Arbiter logic without external dependencies.

## Key Assertions

Tests verify:

1. **Correctness**: Task results match expected outputs
2. **State transitions**: Tasks progress properly through their lifecycle
3. **Completion**: All tasks complete (or are properly terminated)
4. **Resource management**: Worker resources are properly allocated and released
5. **Ordering**: Sequential operations happen in the correct order
6. **Timeout handling**: Tasks can be killed before natural completion

## Writing New Tests

When adding new tests for Arbiter, follow these guidelines:

1. Use the existing fixture pattern for setup/teardown
2. Test one specific feature or pattern per test case
3. Include assertions for both functionality and resource management
4. Clean up resources in each test
5. Use descriptive test names that reflect what is being tested