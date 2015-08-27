"""
local.py

Helpers to allow use asyncio on werkzeug library.
"""
import inspect
from functools import wraps
from asyncio import futures
from asyncio.coroutines import CoroWrapper
from asyncio.tasks import Task

__author__ = 'alfred'


def identify_future(fut=None):
    """
    Function to identify a task or future.

    :param fut: Future to identify. Optional. Default value is None.
                When it is None it use :meth:``asyncio.tasks.Task.current_task`` method.
    :type fut: asyncio.Future or None
    :return: int
    """
    if fut is None:
        fut = Task.current_task()
    return id(fut)


def patch_local(local):
    """
    Helper to make :class:`werkzeug.local.Local` or :class:`werkzeug.local.LocalStack`
    working with asyncio eventloop.

    :param local: Local to patch
    :type local: werkzeug.local.Local or werkzeug.local.LocalStack
    """
    object.__setattr__(local, '__ident_func__', identify_future)


class ContextCoroWrapper(CoroWrapper):
    """
    Coroutine wrapper to keep context on coroutines execution.
    """

    def __init__(self, gen, func, ctx):
        """
        :param gen: It must be a generator function, usually a coroutine.
        :param func: Original function that created generator.
        :param ctx: It must be a callable that returns a context manager.
        :return:
        """
        super(ContextCoroWrapper, self).__init__(gen, func)
        self.ctx = ctx()

    def send(self, value):
        with self.ctx:
            return super(ContextCoroWrapper, self).send(value)

    def __next__(self):
        with self.ctx:
            return super(ContextCoroWrapper, self).__next__()


def context_coroutine(func, ctx):
    """Decorator factory to run coroutines inside context.

    **Example:**

    .. code-block:: python

        def _get_app_context():
            return current_app.app_context()

        app_coroutine = partial(context_coroutine, ctx=_get_app_context)
    """
    if not inspect.isgeneratorfunction(func):

        @wraps(func)
        def coro(*args, **kw):
            res = func(*args, **kw)
            if isinstance(res, futures.Future) or inspect.isgenerator(res):
                res = yield from res
            return res

    else:
        coro = func

    @wraps(func)
    def wrapper(*args, **kwargs):
        w = ContextCoroWrapper(coro(*args, **kwargs), func, ctx)
        if w._source_traceback:
            del w._source_traceback[-1]
        w.__name__ = func.__name__
        if hasattr(func, '__qualname__'):
            w.__qualname__ = func.__qualname__
        w.__doc__ = func.__doc__
        return w

    wrapper._is_coroutine = True  # For iscoroutinefunction().

    return wrapper
