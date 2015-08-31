import asyncio
import socket
import os
import sys
from aiohttp.wsgi import WSGIServerHttpProtocol
from werkzeug._internal import _log
from werkzeug.serving import select_ip_version

__author__ = 'alfred'


def make_server(host, port, app=None, threaded=False, processes=1,
                request_handler=None, passthrough_errors=False,
                ssl_context=None, loop=None):
    if threaded or processes > 1:
        raise ValueError("Multi-thread or process servers not supported.")

    loop = loop or asyncio.get_event_loop()
    asyncio.async(asyncio.get_event_loop().create_server(lambda: WSGIServerHttpProtocol(app, readpayload=True),
                                                         host, port),
                  loop=loop)


def run_simple(hostname, port, application, use_reloader=False,
               use_debugger=False, use_evalex=True,
               extra_files=None, reloader_interval=1,
               reloader_type='auto', threaded=False, processes=1,
               request_handler=None, static_files=None,
               passthrough_errors=False, ssl_context=None, loop=None):
    """Start a WSGI application. Optional features include a reloader,
    multithreading and fork support.

    This function has a command-line interface too::

        python -m werkzeug.serving --help

    .. versionadded:: 0.5
       `static_files` was added to simplify serving of static files as well
       as `passthrough_errors`.

    .. versionadded:: 0.6
       support for SSL was added.

    .. versionadded:: 0.8
       Added support for automatically loading a SSL context from certificate
       file and private key.

    .. versionadded:: 0.9
       Added command-line interface.

    .. versionadded:: 0.10
       Improved the reloader and added support for changing the backend
       through the `reloader_type` parameter.  See :ref:`reloader`
       for more information.

    :param hostname: The host for the application.  eg: ``'localhost'``
    :param port: The port for the server.  eg: ``8080``
    :param application: the WSGI application to execute
    :param use_reloader: should the server automatically restart the python
                         process if modules were changed?
    :param use_debugger: should the werkzeug debugging system be used?
    :param use_evalex: should the exception evaluation feature be enabled?
    :param extra_files: a list of files the reloader should watch
                        additionally to the modules.  For example configuration
                        files.
    :param reloader_interval: the interval for the reloader in seconds.
    :param reloader_type: the type of reloader to use.  The default is
                          auto detection.  Valid values are ``'stat'`` and
                          ``'watchdog'``. See :ref:`reloader` for more
                          information.
    :param threaded: should the process handle each request in a separate
                     thread?
    :param processes: if greater than 1 then handle each request in a new process
                      up to this maximum number of concurrent processes.
    :param request_handler: optional parameter that can be used to replace
                            the default one.  You can use this to replace it
                            with a different
                            :class:`~BaseHTTPServer.BaseHTTPRequestHandler`
                            subclass.
    :param static_files: a dict of paths for static files.  This works exactly
                         like :class:`SharedDataMiddleware`, it's actually
                         just wrapping the application in that middleware before
                         serving.
    :param passthrough_errors: set this to `True` to disable the error catching.
                               This means that the server will die on errors but
                               it can be useful to hook debuggers in (pdb etc.)
    :param ssl_context: an SSL context for the connection. Either an
                        :class:`ssl.SSLContext`, a tuple in the form
                        ``(cert_file, pkey_file)``, the string ``'adhoc'`` if
                        the server should automatically create one, or ``None``
                        to disable SSL (which is the default).
    """
    loop = loop or asyncio.get_event_loop()

    if use_debugger:
        raise NotImplemented("Debugger not implemented with asyncio")
    if static_files:
        raise NotImplemented("Static files not implemented with asyncio")

    def inner(loop):
        make_server(hostname, port, application, threaded,
                    processes, request_handler,
                    passthrough_errors, ssl_context, loop)

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        display_hostname = hostname != '*' and hostname or 'localhost'
        if ':' in display_hostname:
            display_hostname = '[%s]' % display_hostname
        quit_msg = '(Press CTRL+C to quit)'
        _log('info', ' * Running on %s://%s:%d/ %s', ssl_context is None
             and 'http' or 'https', display_hostname, port, quit_msg)
    if use_reloader:
        # Create and destroy a socket so that any exceptions are raised before
        # we spawn a separate Python interpreter and lose this ability.
        address_family = select_ip_version(hostname, port)
        test_socket = socket.socket(address_family, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind((hostname, port))
        test_socket.close()

        from ._reloader import run_with_reloader
        run_with_reloader(inner, extra_files, reloader_interval,
                          reloader_type, loop)
    else:
        inner(loop)
        loop.run_forever()


def run_with_reloader(*args, **kwargs):
    # People keep using undocumented APIs.  Do not use this function
    # please, we do not guarantee that it continues working.
    from ._reloader import run_with_reloader
    return run_with_reloader(*args, **kwargs)


def main():
    '''A simple command-line interface for :py:func:`run_simple`.'''

    # in contrast to argparse, this works at least under Python < 2.7
    import optparse
    from werkzeug.utils import import_string

    parser = optparse.OptionParser(
        usage='Usage: %prog [options] app_module:app_object')
    parser.add_option('-b', '--bind', dest='address',
                      help='The hostname:port the app should listen on.')
    parser.add_option('-d', '--debug', dest='use_debugger',
                      action='store_true', default=False,
                      help='Use Werkzeug\'s debugger.')
    parser.add_option('-r', '--reload', dest='use_reloader',
                      action='store_true', default=False,
                      help='Reload Python process if modules change.')
    options, args = parser.parse_args()

    hostname, port = None, None
    if options.address:
        address = options.address.split(':')
        hostname = address[0]
        if len(address) > 1:
            port = address[1]

    if len(args) != 1:
        sys.stdout.write('No application supplied, or too much. See --help\n')
        sys.exit(1)
    app = import_string(args[0])

    run_simple(
        hostname=(hostname or '127.0.0.1'), port=int(port or 5000),
        application=app, use_reloader=options.use_reloader,
        use_debugger=options.use_debugger
    )

if __name__ == '__main__':
    main()
