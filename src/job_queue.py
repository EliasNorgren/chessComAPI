import queue
import threading

_queues = {}     # job_id -> queue.Queue of job dicts
_results = {}    # job_id -> list[result | None]
_events = {}     # job_id -> threading.Event
_callbacks = {}  # job_id -> callable(completed_count)
_lock = threading.Lock()


def create_job(job_id: str, jobs: list):
    with _lock:
        q = queue.Queue()
        for job in jobs:
            q.put(job)
        _queues[job_id] = q
        _results[job_id] = [None] * len(jobs)
        _events[job_id] = threading.Event()
        _callbacks[job_id] = None


def set_progress_callback(job_id: str, callback):
    with _lock:
        _callbacks[job_id] = callback


def dequeue(job_id: str, count: int) -> list:
    q = _queues.get(job_id)
    if not q:
        return []
    items = []
    for _ in range(count):
        try:
            items.append(q.get_nowait())
        except queue.Empty:
            break
    return items


def submit_results(job_id: str, results: list):
    with _lock:
        result_list = _results[job_id]
        for item in results:
            result_list[item['index']] = item['result']
        completed = sum(1 for r in result_list if r is not None)
        cb = _callbacks.get(job_id)
    if cb:
        cb(completed)
    with _lock:
        if all(r is not None for r in _results[job_id]):
            _events[job_id].set()


def wait_for_completion(job_id: str, timeout: int = 600) -> list:
    event = _events.get(job_id)
    if event:
        event.wait(timeout=timeout)
    return _results.get(job_id, [])


def cleanup(job_id: str):
    with _lock:
        _queues.pop(job_id, None)
        _results.pop(job_id, None)
        _events.pop(job_id, None)
        _callbacks.pop(job_id, None)
