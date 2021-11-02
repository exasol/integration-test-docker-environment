from multiprocessing import Process, Queue
from typing import Callable


def process_main(queue: Queue, func: Callable):
    try:
        result = func()
        queue.put(("result", result))
    except Exception as e:
        queue.put(("exception", e))


def run_in_process(func):
    queue = Queue()
    p1 = Process(target=process_main, args=(queue, func))
    p1.start()
    p1.join()
    result = queue.get()
    if result[0] == "result":
        return result[1]
    else:
        raise result[1]
