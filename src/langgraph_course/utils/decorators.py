# ---------------------------------------------------------------------------
# timed_node decorator (mirrors tickets.py pattern)
# ---------------------------------------------------------------------------
import functools
import time
from typing import Callable, Any, Dict


def timed_node(node_name: str) -> Callable:
    """Decorator that records per-node latency and appends to paths_taken."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Dict:
            state = args[1]
            start = time.monotonic()
            result = func(*args, **kwargs)
            elapsed = time.monotonic() - start

            latencies = dict(state.get('latencies', {}))
            latencies[node_name] = elapsed
            result['latencies'] = latencies

            paths = list(state.get('paths_taken', []))
            paths.append(node_name)
            result['paths_taken'] = paths

            return result
        return wrapper
    return decorator
