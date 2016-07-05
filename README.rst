
|travis-master| |coverall-master| |doc-master| |pypi-downloads| |pypi-lastrelease| |python-versions|
|project-status| |project-license| |project-format| |project-implementation|

.. |travis-master| image:: https://travis-ci.org/alfred82santa/aiowerkzeug.svg?branch=master
    :target: https://travis-ci.org/alfred82santa/aiowerkzeug

.. |coverall-master| image:: https://coveralls.io/repos/alfred82santa/aiowerkzeug/badge.svg?branch=master&service=github
    :target: https://coveralls.io/r/alfred82santa/aiowerkzeug?branch=master

.. |doc-master| image:: https://readthedocs.org/projects/aiowerkzeug/badge/?version=latest
    :target: https://readthedocs.org/projects/aiowerkzeug/?badge=latest
    :alt: Documentation Status

.. |pypi-downloads| image:: https://img.shields.io/pypi/dm/aiowerkzeug.svg
    :target: https://pypi.python.org/pypi/aiowerkzeug/
    :alt: Downloads

.. |pypi-lastrelease| image:: https://img.shields.io/pypi/v/aiowerkzeug.svg
    :target: https://pypi.python.org/pypi/aiowerkzeug/
    :alt: Latest Version

.. |python-versions| image:: https://img.shields.io/pypi/pyversions/aiowerkzeug.svg
    :target: https://pypi.python.org/pypi/aiowerkzeug/
    :alt: Supported Python versions

.. |project-status| image:: https://img.shields.io/pypi/status/aiowerkzeug.svg
    :target: https://pypi.python.org/pypi/aiowerkzeug/
    :alt: Development Status

.. |project-license| image:: https://img.shields.io/pypi/l/aiowerkzeug.svg
    :target: https://pypi.python.org/pypi/aiowerkzeug/
    :alt: License

.. |project-format| image:: https://img.shields.io/pypi/format/aiowerkzeug.svg
    :target: https://pypi.python.org/pypi/aiowerkzeug/
    :alt: Download format

.. |project-implementation| image:: https://img.shields.io/pypi/implementation/aiowerkzeug.svg
    :target: https://pypi.python.org/pypi/aiowerkzeug/
    :alt: Supported Python implementations

===========
aiowerkzeug
===========

Library to make werkzeug working with asyncio.

---------
Changelog
---------

Version 0.2.0
=============

* Use Python 3.5 async syntax.

* New :func:`~keep_context_factory`. It works like :func:`~context_coroutine`,
  but simple code.

* Async version of Local, LocalStack and LocalManager. They implement `__release_local__` method.

--------
Features
--------

* Async versions of Local, LocalStack and LocalManager.

* Locals work on asyncio Tasks. :class:`werkzeug.local.Local` or :class:`werkzeug.local.LocalStack` must be patched
  with :func:`aiowerkzeug.local.patch_local`

  Patched :class:`werkzeug.local.Local` or :class:`werkzeug.local.LocalStack` use current :class:`asyncio.tasks.Task`
  to determine context.

* Decorator factory to mark coroutines to run in a context. Useful for Flask. It allows to run corountines
  in new :class:`asyncio.tasks.Task` inside a specific context.

  For example, in Flask to run coroutines in Application context it is possible to create a decorator like that:

  .. code-block:: python

        def _get_app_context():
            return current_app.app_context()

        app_coroutine = partial(context_coroutine, ctx=_get_app_context)

        @app_coroutine
        def foo_bar():
            print(current_app.debug)

        @flask_app.route('/')
        def caller():
            asyncio.ensure_future(foo_bar())

* Asyncio HTTP server runner with reload

  .. code-block:: bash

    $ python aiowerkzeug/serving.py --reload app_test.app

----
TODO
----

* Form parser
* Debug middleware
* Static files middleware
