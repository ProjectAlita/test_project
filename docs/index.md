# Arbiter Documentation

## Overview

Arbiter is a distributed task queue system using Redis as a broker. It consists of two main components:

1. **Arbiter**: The job scheduler that maintains the state of all jobs and retrieves results.
2. **Minion**: The worker component that executes tasks.

This documentation provides comprehensive information about the Arbiter system architecture, usage patterns, API reference, and testing procedures.

## Contents

### Architecture

- [Architecture Overview](ARCHITECTURE.md): Detailed explanation of the Arbiter system architecture, including components, communication flow, and design principles.

### User Guides

- [Usage Guide](USAGE.md): Comprehensive guide on how to use Arbiter, including setup, task creation, running workers, executing tasks, and advanced features.

### API Reference

- [API Reference](API_REFERENCE.md): Detailed documentation of all classes, methods, and their parameters in the Arbiter system.

### Testing

- [Test Documentation](TESTS.md): Information about the test suite, how to run tests, and what each test verifies.

## Features

- Distributed task execution across worker nodes
- Multiple worker pools with different capabilities
- Task synchronization and status tracking
- Various task patterns:
  - Single tasks
  - Task groups ("squad")
  - Sequential tasks ("pipe")
  - Callbacks and finalizers
- Worker management and monitoring
- Task termination and cleanup
- Event-driven communication via Redis

## Requirements

- Python 3.6+
- Redis server
- Required Python packages (see requirements.txt)

## Installation

```bash
git clone https://github.com/carrier-io/arbiter.git
cd arbiter
python setup.py install
```

## Quick Start

### Start a Minion (Worker)

```python
from arbiter import RedisEventNode, Minion

# Configure event node
event_node = RedisEventNode(
    host="localhost", 
    port=6379, 
    password="", 
    event_queue="tasks"
)

# Create minion
app = Minion(event_node, queue="default")

# Define a task
@app.task(name="add")
def add(x, y):
    return x + y

# Start worker with 3 slots
app.run(workers=3)
```

### Use Arbiter (Client)

```python
from arbiter import RedisEventNode, Arbiter

# Configure event node (same parameters as minion)
event_node = RedisEventNode(
    host="localhost", 
    port=6379, 
    password="", 
    event_queue="tasks"
)

# Create arbiter
arbiter = Arbiter(event_node)

# Execute task
task_ids = arbiter.apply("add", task_args=[5, 3])

# Wait for and print result
for message in arbiter.wait_for_tasks(task_ids):
    print(f"Result: {message['result']}")  # Output: Result: 8
```

## License

Arbiter is licensed under the Apache License 2.0 - see the LICENSE file for details.