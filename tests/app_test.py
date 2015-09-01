import asyncio

__author__ = 'alfred'


def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    asyncio.sleep(1)
    return [b'hello']
