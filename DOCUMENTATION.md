# Arbiter Codebase Documentation

## Overview
Arbiter is a lightweight distributed task management framework using Redis as a message broker. It consists of two main components:
- **Arbiter**: Initiates and monitors asynchronous tasks.
- **Minion**: Executes tasks declared by the Arbiter.

Communication is based on event nodes (e.g., RedisEventNode) for sending task requests and status updates.

## Project Structure
```
arbiter/                 # Core library package
  arbiter.py             # Arbiter class (task initiator)
  minion.py              # Minion class (worker)
  task.py                # Task descriptor
  log.py                 # Logging utilities
  eventnode/             # Event node implementations and API
    base.py              # Abstract base for event nodes
    tools.py             # Common utilities for event nodes
    hooks.py             # Hook implementations
    mock.py              # In-memory mock event node for testing
    __init__.py          # Factory (make_event_node)
  tasknode/              # Task node: starts/stops tasks, monitors workers
    tasknode.py          # TaskNode class (core task lifecycle)
    watcher.py           # Watches task status events
    housekeeper.py       # Cleans up stale or orphaned tasks
    tools.py             # Utilities for tasknode
    __init__.py
tests/                   # Test suite for Arbiter and Minion
  test_arbiter.py        # Tests for Arbiter behaviors
  minion.py              # Example / tests for Minion
  README.md              # Instructions for running tests
AGENTS.md                # Development environment notes
README.md                # Project overview and quickstart guide
setup.py                 # Package setup
requirements.txt         # Runtime dependencies
version.txt              # Base version string
LICENSE                  # Apache 2.0 license
```

## Core Components

### arbiter.arbiter.Ar biter
- Manages task submission, status tracking, and result retrieval.
- Key methods:
  - `apply(name, queue, tasks_count, task_args, task_kwargs, sync)`: Submit tasks and optionally wait for results.
  - `wait_for_tasks(task_keys)`: Generator yielding task status dicts as tasks complete.
  - `status(task_key)`: Query status of a single task or a task group.
  - `kill(task_key)`, `kill_group(group_id)`: Cancel running tasks.
  - `workers()`: Inspect worker pool states.

### arbiter.minion.Minion
- Registers and executes tasks defined via the `@app.task` decorator.
- Manages a pool of worker processes.
- Listens for task requests from an event node and returns results upon completion.

### arbiter.task.Task
- Descriptor for task requests sent by the Arbiter.
- Encapsulates task name, queue (worker pool), count, args, and kwargs.

## Event Nodes
Event nodes abstract the messaging layer between Arbiter and Minion:
- **RedisEventNode** (in `eventnode/tools.py`): Uses Redis lists/pubsub for task requests and statuses.
- **MockEventNode** (`eventnode/mock.py`): In-memory implementation for testing.
- Factory `make_event_node(...)` chooses based on URI or parameters.

## TaskNode and Subcomponents
`TaskNode` wraps event node to handle low-level task lifecycle:
- Starts and stops tasks on Minion via `start_task` / `stop_task`.
- `TaskWatcher` subscribes to status events and updates internal state.
- `Housekeeper` periodically cleans stale tasks.

## Logging
All components use `arbiter.log` for structured logging. Configuration can be customized at application startup.

## Testing
Run tests with pytest:
```bash
pytest --cov=arbiter
```
Use the `MockEventNode` to simulate message passing in unit tests.

## Contribution
- Follow PEP8 and existing code style.
- Run `pre-commit` hooks if configured:
  ```bash
  pre-commit run --all-files
  ```

For more details, refer to individual module docstrings in the code.