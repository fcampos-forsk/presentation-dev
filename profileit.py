import cProfile
import functools
from datetime import datetime
from contextlib import contextmanager
from dataclasses import dataclass
import time


def profileit(
    func=None,
    /, *,
    file_format='profiling/{func.__name__}-{dt}.profile',
):
    """
    Creates a cProfile file for each call to a function.

    Le répertoire doit déjà exister!

    Visualization with command 'snakeviz -s profiling'
    """
    def decorator(func):
        @functools.wraps(func)
        def decorated(*args, **kwargs):
            prof = cProfile.Profile()
            with timeit() as timing:
                retval = prof.runcall(func, *args, **kwargs)
            prof.dump_stats(file_format.format(
                func=func,
                dt=datetime.now(),
                timing=timing,
                args=args,
                kwargs=kwargs,
            ))
            return retval

        return decorated
    return decorator(func) if callable(func) else decorator


@dataclass
class Timing:
    start: float = None
    stop: float = None
    duration: float = None


def test_func():
    time.sleep(1);
    return;

@contextmanager
def timeit():
    t = Timing(start=time())
    try:
        yield t
    finally:
        end = time()
        t.stop = end
        t.duration = end - t.start

for i in range(5):
    test_func()