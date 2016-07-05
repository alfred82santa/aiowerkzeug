"""
local.py

Helpers to allow use asyncio on werkzeug library.
"""
import inspect
from functools import wraps, partial
from asyncio import futures, Task, ensure_future
from asyncio.coroutines import CoroWrapper
from werkzeug.local import Local, LocalStack, LocalManager


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


def keep_context_factory(func, ctx):
    """Decorator factory to run coroutines or async functions inside context.

    Simplified version of :meth:`~context_coroutine` factory. It must work in same
    way. But its code is more simple.

    **Example:**

    .. code-block:: python

        def _get_app_context():
            return current_app.app_context()

        keep_app_context = partial(keep_context_factory, ctx=_get_app_context)
    """

    @wraps(func)
    def inner(*args, **kwargs):
        ctx_obj = ctx()

        async def wrapper():
            with ctx_obj:
                return await func(*args, **kwargs)

        return wrapper()

    return inner


def async_task_with_context(fut, ctx, callback=None, loop=None):

    decorator = partial(keep_context_factory, ctx=ctx)

    @decorator
    async def inner():
        try:
            return await fut
        finally:
            if callback:
                callback()

    return ensure_future(inner(), loop=loop)


class AsyncLocal(Local):

    def __init__(self):
        super(AsyncLocal, self).__init__()
        object.__setattr__(self, '__ident_func__', identify_future)

    def __release_local__(self, fut=None):
        self.__storage__.pop(self.__ident_func__(fut=fut), None)


class AsyncLocalStack(LocalStack):

    def __init__(self):
        self._local = AsyncLocal()

    def __release_local__(self, fut=None):
        self._local.__release_local__(fut=fut)


class AsyncLocalManager(LocalManager):

    def make_task_with_ctx_factory(self, ctx, loop=None):
        return partial(async_task_with_context, ctx=ctx, callback=self.cleanup, loop=loop)
