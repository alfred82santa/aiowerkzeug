import asyncio
from functools import partial
from asyncio.coroutines import coroutine
from asyncio.futures import Future
from asyncio.tasks import Task
from asynctest.case import TestCase
from werkzeug.local import Local, LocalStack
from aiowerkzeug.local import identify_future, patch_local, context_coroutine

__author__ = 'alfred'


class IdentifyTest(TestCase):

    use_default_loop = True

    @coroutine
    def test_identfy_current_task(self):
        self.assertEqual(id(Task.current_task()), identify_future())

    @coroutine
    def test_identfy_future(self):
        fut = Future()
        self.assertEqual(id(fut), identify_future(fut))

    @coroutine
    def test_identfy_task_on_loop(self):

        @coroutine
        def other_task():
            return identify_future()

        fut = asyncio.async(other_task())
        yield from fut
        self.assertNotEqual(fut.result(), identify_future())


class PatchLocalTest(TestCase):

    use_default_loop = True

    @coroutine
    def test_coroutine_local(self):

        ctx = Local()
        patch_local(ctx)

        @coroutine
        def other_context():
            ctx.test = 45
            return ctx.test

        ctx.test = 40

        fut = asyncio.async(other_context())
        yield from fut
        self.assertEqual(ctx.test, 40)
        self.assertNotEqual(ctx.test, fut.result())
        self.assertEqual(fut.result(), 45)

    @coroutine
    def test_coroutine_localstack(self):

        ctx = LocalStack()
        patch_local(ctx)

        @coroutine
        def other_context():
            ctx.push(45)
            return ctx.top

        ctx.push(40)

        fut = asyncio.async(other_context())
        yield from fut
        self.assertEqual(ctx.top, 40)
        self.assertNotEqual(ctx.top, fut.result())
        self.assertEqual(fut.result(), 45)


class LocalContextCoroutineTest(TestCase):

    use_default_loop = True

    class CtxManager:

        def __init__(self, local):
            self.local = local

        def __enter__(self):
            self.local.test = 45

        def __exit__(self, exc_type, exc_val, exc_tb):
            try:
                del self.local.test
            except AttributeError:
                pass

    @coroutine
    def test_func_context_local(self):

        ctx = Local()
        patch_local(ctx)
        ctxman = self.CtxManager(ctx)
        test_coroutine = partial(context_coroutine, ctx=lambda: ctxman)

        @test_coroutine
        def other_context():
            return ctx.test

        fut = asyncio.async(other_context())
        yield from fut
        self.assertFalse(hasattr(ctx, 'test'))
        self.assertEqual(fut.result(), 45)

    @coroutine
    def test_coroutine_context_local(self):

        ctx = Local()
        patch_local(ctx)
        ctxman = self.CtxManager(ctx)
        test_coroutine = partial(context_coroutine, ctx=lambda: ctxman)

        @test_coroutine
        @coroutine
        def other_context():
            return ctx.test

        fut = asyncio.async(other_context())
        yield from fut
        self.assertFalse(hasattr(ctx, 'test'))
        self.assertEqual(fut.result(), 45)

    @coroutine
    def test_generator_context_local(self):

        ctx = Local()
        patch_local(ctx)
        ctxman = self.CtxManager(ctx)
        test_coroutine = partial(context_coroutine, ctx=lambda: ctxman)

        @coroutine
        def gen():
            yield
            return ctx.test

        @test_coroutine
        def other_context():
            return gen()

        fut = asyncio.async(other_context())
        yield from fut
        self.assertFalse(hasattr(ctx, 'test'))
        self.assertEqual(fut.result(), 45)

    @coroutine
    def test_send_context_local(self):

        ctx = Local()
        patch_local(ctx)
        ctxman = self.CtxManager(ctx)
        test_coroutine = partial(context_coroutine, ctx=lambda: ctxman)

        @test_coroutine
        def gen():
            return ctx.test

        @test_coroutine
        def other_context():
            res = yield from gen()
            return res

        gene = other_context()
        try:
            gene.send(None)
        except StopIteration as ex:
            self.assertEqual(ex.value, 45)
