# Arbiter Usage Guide

This guide provides comprehensive instructions and examples for using the Arbiter distributed task queue system.

## Table of Contents
1. [Setup](#setup)
2. [Creating Tasks](#creating-tasks)
3. [Running Workers](#running-workers)
4. [Executing Tasks](#executing-tasks)
5. [Task Patterns](#task-patterns)
6. [Managing Task State](#managing-task-state)
7. [Error Handling](#error-handling)
8. [Advanced Features](#advanced-features)

## Setup

### Prerequisites
- Python 3.6+
- Redis server

### Installation

Clone the repository and install the package:
```bash
git clone https://github.com/carrier-io/arbiter.git
cd arbiter
python setup.py install
```

### Starting Redis

For development, you can run Redis in a Docker container:
```bash
docker run -d --rm --hostname arbiter-redis --name arbiter-redis \
           -p 6379:6379 redis:alpine redis-server
```

For production environments, configure a proper Redis instance with appropriate security settings.

## Creating Tasks

### Minion Setup

Create a minion to define and execute tasks:

```python
from arbiter import RedisEventNode
from arbiter import Minion

# Configure event communication
event_node = RedisEventNode(
    host="localhost", 
    port=6379, 
    password="", 
    event_queue="tasks"
)

# Create a minion for the "default" queue
app = Minion(event_node, queue="default")
```

### Task Definition

Define tasks using the decorator pattern:

```python
@app.task(name="simple_add")
def add(x, y):
    return x + y

@app.task(name="process_data")
def process_data(items, multiplier=1):
    return [item * multiplier for item in items]
```

Tasks can accept both positional and keyword arguments, and can return any serializable result.

## Running Workers

Start worker processes to execute tasks:

```python
if __name__ == "__main__":
    # Start 3 worker processes for this minion
    app.run(workers=3)
```

The `workers` parameter determines how many concurrent tasks this minion can process.

## Executing Tasks

### Arbiter Setup

Create an Arbiter to schedule and track tasks:

```python
from arbiter import RedisEventNode
from arbiter import Arbiter

# Configure event communication (same as minion)
event_node = RedisEventNode(
    host="localhost", 
    port=6379, 
    password="", 
    event_queue="tasks"
)

# Create the arbiter
arbiter = Arbiter(event_node)
```

### Basic Task Execution

Execute a simple task:

```python
# Execute the 'simple_add' task with arguments 5 and 3
task_ids = arbiter.apply(
    "simple_add", 
    task_args=[5, 3], 
    queue="default"
)

# Get the result
result = arbiter.status(task_ids[0])
print(f"Result: {result['result']}")  # Output: Result: 8
```

### Synchronous Execution

Wait for task completion:

```python
task_ids = arbiter.apply(
    "simple_add", 
    task_args=[10, 20],
    sync=True  # Wait for completion
)

# The result is directly available
print(f"Result: {task_ids[1]['result']}")  # Output: Result: 30
```

### Multiple Task Instances

Execute the same task multiple times:

```python
task_ids = arbiter.apply(
    "simple_add", 
    task_args=[5, 5],
    tasks_count=5  # Execute this task 5 times
)

# Wait for all tasks to complete
for result in arbiter.wait_for_tasks(task_ids):
    print(f"Task completed with result: {result['result']}")
```

## Task Patterns

### Task Group (Squad)

Execute a group of tasks together, ensuring enough workers are available:

```python
from arbiter import Task

# Define the tasks
task1 = Task("process_data", task_args=[[1, 2, 3]])
task2 = Task("process_data", task_args=[[4, 5, 6]], task_kwargs={"multiplier": 2})
task3 = Task("simple_add", task_args=[7, 8])

# Create a squad (ensures sufficient workers)
group_id = arbiter.squad([task1, task2, task3])

# Check group status
status = arbiter.status(group_id)
print(f"Group status: {status['state']}")  # initiated, running, or done

# Wait until done
while arbiter.status(group_id)['state'] != 'done':
    time.sleep(1)

# Get results from the group
results = [arbiter.status(task_id) for task_id in arbiter.group_state[group_id]]
```

### Task Pipeline (Pipe)

Execute tasks sequentially, passing results between them:

```python
from arbiter import Task

# Define tasks for the pipeline
task1 = Task("process_data", task_args=[[1, 2, 3, 4, 5]])
task2 = Task("process_data", task_kwargs={"multiplier": 2})  # Will receive task1's output

# Execute tasks in sequence
results = []
for result in arbiter.pipe([task1, task2]):
    results.append(result)
```

### Callbacks

Execute a task after a group completes:

```python
from arbiter import Task

# Define the main tasks
tasks = [
    Task("process_data", task_args=[[1, 2, 3]]),
    Task("simple_add", task_args=[10, 20])
]

# Define a callback task
callback = Task("aggregate_results")

# Execute with callback
group_id = arbiter.group(tasks, callback=callback)
```

### Finalizers

Execute a task when all others complete, regardless of success/failure:

```python
from arbiter import Task

# Define the main tasks
tasks = [
    Task("process_data", task_args=[[1, 2, 3]]),
    Task("simple_add", task_args=[10, 20])
]

# Define a finalizer task
cleanup = Task("cleanup_resources", task_type="finalize")
tasks.append(cleanup)

# Execute with finalizer
group_id = arbiter.group(tasks)
```

## Managing Task State

### Checking Task Status

```python
# Check status of a single task
status = arbiter.status(task_id)
print(f"Status: {status['state']}")  # initiated, running, or done

if status['state'] == 'done':
    print(f"Result: {status['result']}")
```

### Checking Worker Status

```python
# Get status of all worker pools
workers = arbiter.workers()
print(workers)  # Shows active, available, and total workers for each pool
```

### Stopping Tasks

```python
# Kill a running task
arbiter.kill(task_id)

# Kill an entire task group
arbiter.kill_group(group_id)
```

### Cleanup

```python
# Close the arbiter when done
arbiter.close()
```

## Error Handling

Tasks that raise exceptions will have the exception stored in the result:

```python
@app.task(name="failing_task")
def failing_task():
    raise ValueError("Something went wrong!")

# Execute the failing task
task_ids = arbiter.apply("failing_task", sync=True)

# The exception will be raised when accessing the result
try:
    result = task_ids[1]['result']
except Exception as e:
    print(f"Task failed: {e}")
```

## Advanced Features

### Task Timeout

Set a timeout for finalizer tasks:

```python
cleanup = Task(
    "cleanup", 
    task_type="finalize",
    timeout=60  # Run the finalizer after 60 seconds if tasks are still running
)
```

### Custom Task Metadata

```python
task = Task(
    "process_data",
    task_args=[[1, 2, 3]],
    task_kwargs={"meta": {"job_id": "12345"}}
)
```

### Using Different Worker Queues

```python
# Create a minion for a specific queue
cpu_minion = Minion(event_node, queue="cpu_intensive")

# Execute a task on a specific queue
task_ids = arbiter.apply(
    "process_data", 
    task_args=[[1, 2, 3, 4, 5]],
    queue="cpu_intensive"
)
```

### Customizing Worker Properties

```python
# Set custom properties on the minion
cpu_minion = Minion(
    event_node, 
    queue="cpu_intensive"
)

# Configure task execution
cpu_minion.raw_task_node.kill_on_stop = True  # Force-kill stuck tasks
cpu_minion.raw_task_node.task_limit = 2  # Maximum concurrent tasks
```