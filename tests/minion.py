from arbiter import Minion
from time import sleep
import logging


def start_minion(event_node):
    app = Minion(event_node, queue="default")
    #
    app.raw_task_node.multiprocessing_context = "threading"
    app.raw_task_node.result_transport = "memory"
    #
    @app.task(name="add")
    def add(x, y):
        logging.info("Running task 'add'")
        # task that initiate new task within same app
        increment = 0
        for message in app.apply('simple_add', task_args=[3, 4]):
            if isinstance(message, dict):
                increment = message["result"]
        logging.info("sleep done")
        return x + y + increment
    #
    @app.task(name="simple_add")
    def adds(x, y):
        logging.info(f"Running task 'add_small' with params {x}, {y}")
        return x + y
    #
    @app.task(name="add_in_pipe")
    def addp(x, y, upstream=0):
        logging.info("Running task 'add_in_pipe'")
        return x + y + upstream
    #
    @app.task(name="long_running")
    def long_task():
        for _ in range(180):
            sleep(1)
        return "Long Task"
    #
    app.run(workers=10, block=False)
    #
    return app


def stop_minion(app):
    app.raw_task_node.stop()
