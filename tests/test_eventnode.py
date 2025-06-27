#!/usr/bin/python3
# coding=utf-8
# pylint: disable=C0114,C0116
"""
    Unit tests for EventNode functionality
"""
import time
import threading
import pytest

from arbiter.eventnode.mock import MockEventNode
from arbiter.eventnode.tools import make_event_node


def test_subscribe_and_emit():
    node = MockEventNode()
    results = []
    evt = threading.Event()

    def callback(name, payload):
        results.append((name, payload))
        evt.set()

    node.subscribe('foo', callback)
    node.start()
    node.emit('foo', {'a': 1})
    assert evt.wait(timeout=1), 'Callback was not invoked'
    assert results == [('foo', {'a': 1})]
    node.stop()


def test_unsubscribe():
    node = MockEventNode()
    results = []
    evt = threading.Event()

    def callback(name, payload):
        results.append((name, payload))
        evt.set()

    node.subscribe('bar', callback)
    node.unsubscribe('bar', callback)
    node.start()
    node.emit('bar', 'data')
    assert not evt.wait(timeout=0.2), 'Callback should not be invoked after unsubscribe'
    assert results == []
    node.stop()


def test_catch_all_subscription():
    node = MockEventNode()
    results = []
    evt = threading.Event()

    def callback(name, payload):
        results.append((name, payload))
        evt.set()

    node.subscribe(..., callback)
    node.start()
    # Emit first event
    node.emit('evt1', 123)
    assert evt.wait(timeout=1)
    assert results == [('evt1', 123)]
    # Reset and emit another event
    results.clear()
    evt.clear()
    node.emit('evt2', None)
    assert evt.wait(timeout=1)
    assert results == [('evt2', None)]
    node.stop()


def test_before_and_after_hooks():
    node = MockEventNode()
    before_called = []
    after_called = []
    results = []
    evt = threading.Event()

    def cb(name, payload):
        results.append(('cb', name, payload))
        return 'result'

    def before_hook(callback, event_name, event_payload):
        before_called.append((callback, event_name, event_payload))

    def after_hook(callback, callback_result, event_name, event_payload):
        after_called.append((callback, callback_result, event_name, event_payload))
        evt.set()

    node.add_before_callback_hook(before_hook)
    node.add_after_callback_hook(after_hook)
    node.subscribe('baz', cb)
    node.start()
    node.emit('baz', 456)
    assert evt.wait(timeout=1), 'After hook was not invoked'
    assert before_called == [(cb, 'baz', 456)]
    assert results == [('cb', 'baz', 456)]
    assert after_called == [(cb, 'result', 'baz', 456)]
    node.stop()


def test_hmac_validation():
    key = b'secret_key'
    node = MockEventNode(hmac_key=key)
    results = []
    evt = threading.Event()

    def callback(name, payload):
        results.append((name, payload))
        evt.set()

    node.subscribe('secure', callback)
    node.start()
    # Valid event
    node.emit('secure', 'ok')
    assert evt.wait(timeout=1)
    assert results == [('secure', 'ok')]
    # Invalid event: corrupt the data
    data = node.make_event_data('secure', 'bad')
    corrupt = bytearray(data)
    corrupt[0] ^= 0xFF
    node.sync_queue.put(bytes(corrupt))
    # Give time for processing; callback should not be called again
    time.sleep(0.2)
    assert len(results) == 1
    node.stop()


def test_clone_and_make_event_node():
    node = MockEventNode(hmac_key='abc', hmac_digest='sha256', callback_workers=2, log_errors=False)
    clone = node.clone()
    assert isinstance(clone, MockEventNode)
    assert clone.hmac_key == node.hmac_key
    assert clone.hmac_digest == node.hmac_digest
    assert clone.log_errors is False
    # make_event_node with config dict
    new_node = make_event_node({
        'type': 'MockEventNode',
        'hmac_key': 'xyz',
        'hmac_digest': 'sha1',
        'callback_workers': 1,
        'log_errors': True,
    })
    assert isinstance(new_node, MockEventNode)
    assert new_node.hmac_digest == 'sha1'
    assert new_node.log_errors is True
    assert isinstance(new_node.hmac_key, (bytes, type(None)))