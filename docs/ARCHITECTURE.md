# Arbiter Architecture Documentation

## Overview

Arbiter is a distributed task queue system built on Redis that facilitates the execution of tasks across a network of workers. It consists of two primary components: the **Arbiter** (job scheduler) and the **Minion** (worker). The system uses event-driven communication via Redis to coordinate task distribution and execution.

## Core Components

### 1. Arbiter

The Arbiter is responsible for:
- Creating and scheduling tasks
- Tracking task state and status
- Managing task groups and execution patterns
- Handling callbacks and finalizers
- Monitoring worker availability

The Arbiter maintains the state of all tasks in the system and can retrieve results once tasks are completed.

### 2. Minion

The Minion is a worker process that:
- Registers available task functions
- Executes tasks from specified queues
- Reports task results back to the Arbiter
- Manages worker resources and limits

### 3. Task

A Task represents a unit of work to be executed. Tasks have the following properties:
- Name: Identifies the function to execute
- Queue: Specifies which worker pool should handle the task
- Arguments: Data passed to the task function
- Type: Classification of the task (regular, callback, finalizer)
- Metadata: Additional task information

### 4. TaskNode

The TaskNode is the execution engine that:
- Handles task registration
- Starts and stops task execution
- Manages task state and results
- Provides task synchronization mechanisms
- Coordinates worker pools

TaskNode implements different execution modes using either threading or multiprocessing.

### 5. EventNode

The EventNode provides the communication layer that:
- Implements a publish/subscribe mechanism
- Handles event routing between components
- Manages event serialization/deserialization
- Supports security through HMAC authentication

## Communication Flow

1. The Arbiter creates tasks and sends them to Redis
2. Minions poll Redis for tasks in their assigned queues
3. When a Minion finds a task, it executes it
4. Results are returned to Redis
5. The Arbiter retrieves and processes results

## Task Execution Patterns

Arbiter supports several task execution patterns:

### Single Task

```python
arbiter.apply("task_name", queue="default", task_args=["arg1"], task_kwargs={"key": "value"})
```

### Task Group (Squad)

A set of tasks executed together, potentially in parallel:

```python
tasks = [Task("task1"), Task("task2")]
group_id = arbiter.squad(tasks)
```

### Sequential Tasks (Pipe)

A series of tasks executed in sequence, with results from previous tasks passed to subsequent ones:

```python
tasks = [Task("task1"), Task("task2")]
pipe_results = list(arbiter.pipe(tasks))
```

### Callbacks

Tasks executed after a group of tasks completes:

```python
callback = Task("process_results")
group_id = arbiter.group(tasks, callback=callback)
```

### Finalizers

Similar to callbacks but guaranteed to run even if the main tasks fail:

```python
finalizer = Task("cleanup", task_type="finalize")
tasks.append(finalizer)
group_id = arbiter.group(tasks)
```

## Worker Pool Management

Arbiter tracks worker availability across pools:

```python
worker_stats = arbiter.workers()
```

This allows for intelligent task scheduling based on available resources.

## Event Handling System

The EventNode subsystem provides a flexible event handling mechanism that:
- Allows components to publish and subscribe to events
- Supports event filtering and routing
- Provides hooks for pre and post-event processing
- Handles serialization and security

## Task Execution Process

1. Arbiter creates a task with a unique ID
2. Task is announced to all nodes
3. Suitable worker nodes bid to execute the task
4. Arbiter selects a worker and sends task details
5. Worker executes the task
6. Results are captured and stored
7. Arbiter retrieves results

## Concurrency Models

Arbiter supports two concurrency models:
1. Threading: Using Python threads for I/O-bound tasks
2. Multiprocessing: Using separate processes for CPU-bound tasks

## Error Handling

- Task exceptions are captured and reported to the Arbiter
- Tasks can be stopped or killed if needed
- Finalizers ensure cleanup operations run even after failures

## Task Status Lifecycle

Tasks progress through the following states:
1. initiated - Task created and queued
2. running - Task is being executed
3. done - Task has completed or failed

## Security

- HMAC authentication for event messages
- Task validation through approver functions
- Isolation through separate processes

## Architecture Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│              │       │              │       │              │
│   Arbiter    │◄──────►    Redis     │◄──────►   Minion 1   │
│              │       │              │       │              │
└──────┬───────┘       └──────────────┘       └──────────────┘
       │                                               │
       │                                               │
       │                                               │
       │                                      ┌────────▼─────────┐
       │                                      │                  │
       │                                      │   Task Queue 1   │
       │                                      │                  │
       │                                      └──────────────────┘
       │
       │                                      ┌──────────────┐
       │                                      │              │
       └──────────────────────────────────────►   Minion 2   │
                                              │              │
                                              └──────┬───────┘
                                                     │
                                                     │
                                            ┌────────▼─────────┐
                                            │                  │
                                            │   Task Queue 2   │
                                            │                  │
                                            └──────────────────┘
```

## Design Principles

1. **Distribution**: Tasks can be executed across multiple workers
2. **Fault Tolerance**: Tasks can be retried and monitored
3. **Flexibility**: Multiple execution patterns and worker pools
4. **Efficiency**: Optimized task routing based on worker availability
5. **Scalability**: Workers can be added or removed as needed