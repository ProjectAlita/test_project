# Arbiter API Reference

This document provides detailed information about the Arbiter API, including classes, methods, and their parameters.

## Table of Contents

- [Arbiter Class](#arbiter-class)
- [Minion Class](#minion-class)
- [Task Class](#task-class)
- [TaskNode Class](#tasknode-class)
- [EventNode Classes](#eventnode-classes)

---

## Arbiter Class

The `Arbiter` class is responsible for creating, scheduling, and tracking tasks. It maintains the state of all jobs it has created and can retrieve results.

### Constructor

```python
Arbiter(event_node, finalizer_check_interval=10)
```

**Parameters:**

- `event_node` - An EventNode instance used for communication
- `finalizer_check_interval` - Interval (in seconds) to check for finalizer tasks that need to run

### Properties

- `task_node` - Returns the TaskNode instance, creating and starting it if necessary

### Methods

#### `on_task_change(event, data)`

Internal method to handle task status change events.

**Parameters:**
- `event` - Event name
- `data` - Event data containing task information

#### `wait_for_tasks(tasks)`

Wait for a list of tasks to complete and yield their results.

**Parameters:**
- `tasks` - List of task IDs to wait for

**Returns:**
- Generator yielding task results as they complete

#### `add_task(task, sync=False)`

Add a task to the queue for execution.

**Parameters:**
- `task` - Task instance to execute
- `sync` - If True, wait for task completion

**Returns:**
- Generator yielding task IDs and optionally task results

#### `apply(task_name, queue="default", tasks_count=1, task_args=None, task_kwargs=None, sync=False)`

Create and execute a task.

**Parameters:**
- `task_name` - Name of the task to execute
- `queue` - Worker queue to use
- `tasks_count` - Number of task instances to create
- `task_args` - Positional arguments for the task function
- `task_kwargs` - Keyword arguments for the task function
- `sync` - If True, wait for task completion

**Returns:**
- List of task IDs or task results

#### `kill(task_key, sync=True)`

Stop a running task.

**Parameters:**
- `task_key` - ID of the task to stop
- `sync` - If True, wait for the task to stop

#### `kill_group(group_id)`

Stop all tasks in a group.

**Parameters:**
- `group_id` - ID of the group to stop

#### `status(task_key)`

Get the status of a task or group.

**Parameters:**
- `task_key` - Task or group ID to check

**Returns:**
- Dictionary with task or group status

#### `close(waiting_tasks_timeout=None)`

Clean up and stop the arbiter.

**Parameters:**
- `waiting_tasks_timeout` - Maximum time to wait for tasks to complete

#### `workers()`

Get information about available workers.

**Returns:**
- Dictionary with worker pool statistics

#### `squad(tasks, callback=None)`

Execute a group of tasks, ensuring enough workers are available.

**Parameters:**
- `tasks` - List of Task instances to execute
- `callback` - Optional callback Task to execute when all tasks complete

**Returns:**
- Group ID

#### `group(tasks, callback=None)`

Execute a group of tasks in any order.

**Parameters:**
- `tasks` - List of Task instances to execute
- `callback` - Optional callback Task to execute when all tasks complete

**Returns:**
- Group ID

#### `pipe(tasks, persistent_args=None, persistent_kwargs=None)`

Execute tasks sequentially, passing results between them.

**Parameters:**
- `tasks` - List of Task instances to execute in sequence
- `persistent_args` - Arguments to pass to all tasks
- `persistent_kwargs` - Keyword arguments to pass to all tasks

**Returns:**
- Generator yielding results as tasks complete

---

## Minion Class

The `Minion` class is responsible for executing tasks on worker nodes.

### Constructor

```python
Minion(event_node, queue="default")
```

**Parameters:**

- `event_node` - An EventNode instance used for communication
- `queue` - Name of the worker queue this minion belongs to

### Properties

- `task_node` - Returns the TaskNode instance, creating and starting it if necessary

### Methods

#### `wait_for_tasks(tasks)`

Wait for tasks to complete and yield their results.

**Parameters:**
- `tasks` - List of task IDs to wait for

**Returns:**
- Generator yielding task results

#### `add_task(task, sync=False)`

Add a task to the queue for execution.

**Parameters:**
- `task` - Task instance to execute
- `sync` - If True, wait for task completion

**Returns:**
- Generator yielding task IDs and optionally results

#### `apply(task_name, queue=None, tasks_count=1, task_args=None, task_kwargs=None, sync=True)`

Create and execute a task.

**Parameters:**
- `task_name` - Name of the task to execute
- `queue` - Worker queue to use (defaults to minion's queue)
- `tasks_count` - Number of task instances to create
- `task_args` - Positional arguments for the task function
- `task_kwargs` - Keyword arguments for the task function
- `sync` - If True, wait for task completion (default True)

**Returns:**
- Generator yielding task IDs and results

#### `task(*args, **kwargs)`

Decorator for registering task functions.

**Usage:**
```python
@minion.task(name="task_name")
def my_function(arg1, arg2):
    pass
```

#### `run(workers, block=True)`

Start the minion with specified number of worker slots.

**Parameters:**
- `workers` - Number of concurrent tasks this minion can process
- `block` - If True, block until stopped

---

## Task Class

The `Task` class represents a unit of work to be executed.

### Constructor

```python
Task(name, queue='default', tasks_count=1, task_key="", task_type="task", task_args=None, task_kwargs=None, callback=False, callback_queue=None, timeout=-1)
```

**Parameters:**

- `name` - Name of the task function
- `queue` - Worker queue for this task
- `tasks_count` - Number of task instances to create
- `task_key` - Optional unique identifier
- `task_type` - Type of task ("task", "callback", "finalize")
- `task_args` - Positional arguments for the task function
- `task_kwargs` - Keyword arguments for the task function
- `callback` - If True, this task is a callback
- `callback_queue` - Queue for callback results
- `timeout` - Timeout in seconds (for finalize tasks)

### Methods

#### `to_json()`

Convert the task to a JSON-serializable dictionary.

**Returns:**
- Dictionary representing the task

---

## TaskNode Class

The `TaskNode` class is the core execution engine for tasks.

### Constructor

```python
TaskNode(event_node, pool=None, task_limit=None, ident_prefix="", multiprocessing_context="fork", kill_on_stop=False, task_retention_period=3600, housekeeping_interval=60, start_max_wait=3, query_wait=3, watcher_max_wait=3, stop_node_task_wait=3, result_max_wait=3, tmp_path="/tmp/tasknode", result_transport="memory", start_attempts=3, thread_scan_interval=1, task_approver=None)
```

**Parameters:**

- `event_node` - EventNode instance for communication
- `pool` - Worker pool name
- `task_limit` - Maximum number of concurrent tasks
- `ident_prefix` - Prefix for node identifiers
- `multiprocessing_context` - Context for task execution ("fork", "spawn", "threading")
- `kill_on_stop` - If True, kill tasks when stopping
- `task_retention_period` - How long to keep task records
- `housekeeping_interval` - Interval for cleanup operations
- `start_max_wait` - Maximum wait time for task start
- `query_wait` - Wait time for state queries
- `watcher_max_wait` - Maximum wait time for task watchers
- `stop_node_task_wait` - Wait time when stopping node tasks
- `result_max_wait` - Maximum wait time for task results
- `tmp_path` - Path for temporary files
- `result_transport` - How to transport results ("memory", "files", "events")
- `start_attempts` - Number of attempts to start a task
- `thread_scan_interval` - Interval for thread scanning
- `task_approver` - Function to approve task execution

### Methods

#### `start(block=False)`

Start the task node.

**Parameters:**
- `block` - If True, block until stopped

#### `stop(block=True)`

Stop the task node.

**Parameters:**
- `block` - If True, wait for tasks to complete

#### `register_task(func, name=None, approver=None)`

Register a task function.

**Parameters:**
- `func` - Task function to register
- `name` - Name to register the task as
- `approver` - Function to approve task execution

#### `unregister_task(func=None, name=None)`

Unregister a task function.

**Parameters:**
- `func` - Task function to unregister
- `name` - Name of the task to unregister

#### `start_task(name, args=None, kwargs=None, pool=None, meta=None, durable=False)`

Start a task execution.

**Parameters:**
- `name` - Name of the task to execute
- `args` - Positional arguments
- `kwargs` - Keyword arguments
- `pool` - Worker pool to use
- `meta` - Task metadata
- `durable` - If True, task persists after node restart

**Returns:**
- Task ID

#### `stop_task(task_id)`

Stop a running task.

**Parameters:**
- `task_id` - ID of the task to stop

#### `wait_for_task(task_id, timeout=None)`

Wait for a task to complete.

**Parameters:**
- `task_id` - ID of the task to wait for
- `timeout` - Maximum wait time

#### `join_task(task_id, timeout=None)`

Wait for a task and get its result.

**Parameters:**
- `task_id` - ID of the task to join
- `timeout` - Maximum wait time

**Returns:**
- Task result

#### `get_task_status(task_id)`

Get a task's status.

**Parameters:**
- `task_id` - ID of the task

**Returns:**
- Status string ("pending", "running", "stopped")

#### `get_task_meta(task_id)`

Get a task's metadata.

**Parameters:**
- `task_id` - ID of the task

**Returns:**
- Task metadata dictionary

#### `get_task_result(task_id)`

Get a task's result.

**Parameters:**
- `task_id` - ID of the task

**Returns:**
- Task result

#### `subscribe_to_task_statuses(func)`

Subscribe to task status changes.

**Parameters:**
- `func` - Callback function for status changes

#### `query_task_state(task_id=None)`

Query the state of a task.

**Parameters:**
- `task_id` - ID of the task to query

#### `query_pool_state(pool=None)`

Query the state of a worker pool.

**Parameters:**
- `pool` - Name of the pool to query

#### `count_free_workers(pool=None)`

Count available workers in a pool.

**Parameters:**
- `pool` - Name of the pool to query

**Returns:**
- Number of available workers

---

## EventNode Classes

### EventNodeBase

Base class for all event node implementations.

#### Constructor

```python
EventNodeBase(hmac_key=None, hmac_digest="sha512", callback_workers=1, log_errors=True)
```

**Parameters:**

- `hmac_key` - Key for message authentication
- `hmac_digest` - Digest algorithm for authentication
- `callback_workers` - Number of callback worker threads
- `log_errors` - If True, log callback errors

#### Methods

- `clone()` - Create a new event node with same configuration
- `start(emit_only=False)` - Start the event node
- `stop()` - Stop the event node
- `subscribe(event_name, callback)` - Subscribe to events
- `unsubscribe(event_name, callback)` - Unsubscribe from events
- `emit(event_name, payload=None)` - Emit an event

### RedisEventNode

Event node using Redis as transport.

#### Constructor

```python
RedisEventNode(host="localhost", port=6379, db=0, password="", event_queue="tasks", **kwargs)
```

**Parameters:**

- `host` - Redis server hostname
- `port` - Redis server port
- `db` - Redis database
- `password` - Redis password
- `event_queue` - Event queue name
- `**kwargs` - Additional parameters for EventNodeBase

### SocketIOEventNode

Event node using SocketIO as transport.

#### Constructor

```python
SocketIOEventNode(url="http://localhost:8080", **kwargs)
```

**Parameters:**

- `url` - SocketIO server URL
- `**kwargs` - Additional parameters for EventNodeBase

### RabbitMQEventNode

Event node using RabbitMQ as transport.

#### Constructor

```python
RabbitMQEventNode(host="localhost", port=5672, credentials=None, exchange="arbiter", **kwargs)
```

**Parameters:**

- `host` - RabbitMQ server hostname
- `port` - RabbitMQ server port
- `credentials` - Authentication credentials
- `exchange` - Exchange name
- `**kwargs` - Additional parameters for EventNodeBase