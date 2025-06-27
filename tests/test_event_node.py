import pytest
from event_node import EventNode

def test_basic_subscribe_and_emit():
    node = EventNode()
    result = []

    def callback(data):
        result.append(data)

    node.subscribe("test_event", callback)
    node.emit("test_event", "payload")

    assert result == ["payload"]

def test_unsubscribe():
    node = EventNode()
    result = []

    def callback(data):
        result.append(data)

    unsubscribe = node.subscribe("test_event", callback)
    unsubscribe()
    node.emit("test_event", "payload")

    assert result == []

def test_catch_all_subscription():
    node = EventNode()
    result = []

    def callback(event, data):
        result.append((event, data))

    node.subscribe("...", callback)
    node.emit("test_event", "payload")

    assert result == [("test_event", "payload")]

def test_before_and_after_hooks():
    node = EventNode()
    result = []

    def before_hook(event, data):
        result.append(("before", event, data))


    def after_hook(event, data):
        result.append(("after", event, data))


    def callback(data):
        result.append(("callback", data))


    node.before(before_hook)
    node.after(after_hook)
    node.subscribe("test_event", callback)
    node.emit("test_event", "payload")

    assert result == [
        ("before", "test_event", "payload"),
        ("callback", "payload"),
        ("after", "test_event", "payload"),
    ]

def test_hmac_verification():
    node = EventNode(hmac_key="secret")
    result = []

    def callback(data):
        result.append(data)

    node.subscribe("test_event", callback)
    valid_message = node.sign_event("test_event", "payload")
    node.emit("test_event", valid_message)
    assert result == ["payload"]

    # Test with tampered message
    tampered_message = valid_message[:-1] + "x"
    with pytest.raises(ValueError):
        node.emit("test_event", tampered_message)

def test_cloning_and_make_event_node():
    from event_node import make_event_node

    node = make_event_node()
    assert isinstance(node, EventNode)