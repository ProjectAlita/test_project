#!/usr/bin/env pytest
"""
Unit tests for TaskNode: initialization, execution, error handling,
dependency management, cancellation, and state transitions.
"""
import time
import threading
import pytest

from arbiter.tasknode.tasknode import TaskNode
from arbiter.eventnode.mock import MockEventNode


@pytest.fixture
def tasknode():
    # Create a TaskNode with fast intervals for testing
    event_node = MockEventNode()
    # configure short waits for watcher and housekeeping
    node = TaskNode(
        event_node=event_node,
        multiprocessing_context="threading",
        watcher_max_wait=0.1,
        thread_scan_interval=0.05,
        result_max_wait=0.1,
        housekeeping_interval=0.1,
    )
    # start node
    node.start()
    yield node
    # stop node and event_node
    node.stop()
    if event_node.started:
        event_node.stop()


def test_initialization(tasknode):
    # After start, node should be marked started and have an ident
    assert tasknode.started is True
    assert isinstance(tasknode.ident, str) and tasknode.ident
    # stop_event should not be set
    assert not tasknode.stop_event.is_set()


def test_register_and_unregister(tasknode):
    # define dummy task
    def dummy():
        return 'ok'

    # register
    tasknode.register_task(dummy, name='dummy')
    assert 'dummy' in tasknode.task_registry
    # unregister
    tasknode.unregister_task(name='dummy')
    assert 'dummy' not in tasknode.task_registry
    # unregister with func
    tasknode.register_task(dummy)
    name = tasknode.get_callable_name(dummy)
    tasknode.unregister_task(func=dummy)
    assert name not in tasknode.task_registry


def test_task_success_and_result(tasknode):
    # register add
    def add(x, y):
        return x + y
    tasknode.register_task(add, name='add')
    # start task
    task_id = tasknode.start_task('add', args=[2, 3])
    assert task_id is not None
    # wait for completion
    tasknode.wait_for_task(task_id, timeout=1)
    # get status and result
    status = tasknode.get_task_status(task_id)
    # Completed tasks report status 'stopped'
    assert status == 'stopped'
    result = tasknode.get_task_result(task_id)
    assert result == 5


def test_task_exception(tasknode):
    # register failing task
    def fail():
        raise ValueError('oops')
    tasknode.register_task(fail, name='fail')
    task_id = tasknode.start_task('fail')
    assert task_id
    tasknode.wait_for_task(task_id, timeout=1)
    # status should be stopped (task completed with error)
    assert tasknode.get_task_status(task_id) == 'stopped'
    # retrieving result should raise Exception wrapping the original
    with pytest.raises(Exception) as ei:
        _ = tasknode.get_task_result(task_id)
    assert 'oops' in str(ei.value)


def test_task_chaining(tasknode):
    # chain tasks: produce a value then use it
    def produce():
        return 7
    def consume(v):
        return v * 2
    tasknode.register_task(produce, name='produce')
    tasknode.register_task(consume, name='consume')
    # first task
    t1 = tasknode.start_task('produce')
    tasknode.wait_for_task(t1, timeout=1)
    v = tasknode.get_task_result(t1)
    # second task uses result
    t2 = tasknode.start_task('consume', args=[v])
    tasknode.wait_for_task(t2, timeout=1)
    assert tasknode.get_task_result(t2) == 14


def test_task_cancellation(tasknode):
    # long-running task that sleeps
    def long_task():
        time.sleep(2)
        return 'done'
    tasknode.register_task(long_task, name='long')
    t = tasknode.start_task('long')
    # give it a moment to start
    time.sleep(0.1)
    tasknode.stop_task(t)
    tasknode.wait_for_task(t, timeout=1)
    # cancelled tasks return Ellipsis
    res = tasknode.get_task_result(t)
    assert res is ...


def test_status_subscriptions(tasknode):
    events = []
    # subscriber collects status changes (event_name, payload)
    def on_status(event_name, data):
        events.append((data.get('task_id'), data.get('status')))
    tasknode.subscribe_to_task_statuses(on_status)
    # register quick task
    def quick():
        return 1
    tasknode.register_task(quick, name='quick')
    tid = tasknode.start_task('quick')
    tasknode.wait_for_task(tid, timeout=1)
    # expect at least pending and stopped statuses
    statuses = [s for (_id, s) in events if _id == tid]
    assert 'pending' in statuses
    assert 'stopped' in statuses