import asyncio
import os
import sys
from hachiko.hachiko import AIOEventHandler
from werkzeug._internal import _log
from werkzeug._reloader import ReloaderLoop, _find_observable_paths

__author__ = 'alfred'


EVENT_TYPE_MOVED = 'moved'
EVENT_TYPE_DELETED = 'deleted'
EVENT_TYPE_CREATED = 'created'
EVENT_TYPE_MODIFIED = 'modified'


class AIOReloaderLoop(ReloaderLoop):

    def __init__(self, extra_files=None, interval=1, loop=None):
        super(AIOReloaderLoop, self).__init__(extra_files=extra_files, interval=interval)
        self.loop = loop
        self.process = None

    @asyncio.coroutine
    def restart_with_reloader(self):
        """Spawn a new Python interpreter with the same arguments as this one,
        but running the reloader thread.
        """
        _log('info', ' * Restarting with %s' % self.name)
        args = [sys.executable] + sys.argv
        new_environ = os.environ.copy()
        new_environ['WERKZEUG_RUN_MAIN'] = 'true'

        exit_code = 3
        while exit_code == 3:
            self.process = yield from asyncio.create_subprocess_shell(' '.join(args), env=new_environ,
                                                                      cwd=os.getcwd(),
                                                                      stdout=sys.stdout)
            exit_code = yield from self.process.wait()
        return exit_code

    def terminate(self):
        if self.process and self.pid:
            self.process.terminate()


class HachikoReloaderLoop(AIOReloaderLoop):

    def __init__(self, *args, **kwargs):
        super(HachikoReloaderLoop, self).__init__(*args, **kwargs)
        from watchdog.observers import Observer
        self.observable_paths = set()

        @asyncio.coroutine
        def _check_modification(filename):
            if filename in self.extra_files:
                yield from self.trigger_reload(filename)
            dirname = os.path.dirname(filename)
            if dirname.startswith(tuple(self.observable_paths)):
                if filename.endswith(('.pyc', '.pyo')):
                    yield from self.trigger_reload(filename[:-1])
                elif filename.endswith('.py'):
                    yield from self.trigger_reload(filename)

        class _CustomHandler(AIOEventHandler):

            @asyncio.coroutine
            def on_created(self, event):
                yield from _check_modification(event.src_path)

            @asyncio.coroutine
            def on_modified(self, event):
                yield from _check_modification(event.src_path)

            @asyncio.coroutine
            def on_moved(self, event):
                yield from _check_modification(event.src_path)
                yield from _check_modification(event.dest_path)

            @asyncio.coroutine
            def on_deleted(self, event):
                yield from _check_modification(event.src_path)

        reloader_name = Observer.__name__.lower()
        if reloader_name.endswith('observer'):
            reloader_name = reloader_name[:-8]
        reloader_name += ' reloader'

        self.name = reloader_name

        self.observer_class = Observer
        self.event_handler = _CustomHandler(loop=self.loop)
        self.should_reload = asyncio.Event(loop=self.loop)

    @asyncio.coroutine
    def trigger_reload(self, filename):
        # This is called inside an event handler, which means we can't throw
        # SystemExit here. https://github.com/gorakhargosh/watchdog/issues/294
        self.should_reload.set()
        filename = os.path.abspath(filename)
        _log('info', ' * Detected change in %r, reloading' % filename)

    @asyncio.coroutine
    def run(self):
        watches = {}
        observer = self.observer_class()
        observer.start()

        to_delete = set(watches)
        paths = _find_observable_paths(self.extra_files)
        for path in paths:
            if path not in watches:
                try:
                    watches[path] = observer.schedule(
                        self.event_handler, path, recursive=True)
                except OSError as e:
                    message = str(e)

                    if message != "Path is not a directory":
                        # Log the exception
                        _log('error', message)

                    # Clear this path from list of watches We don't want
                    # the same error message showing again in the next
                    # iteration.
                    watches[path] = None
            to_delete.discard(path)
        for path in to_delete:
            watch = watches.pop(path, None)
            if watch is not None:
                observer.unschedule(watch)
        self.observable_paths = paths

        yield from self.should_reload.wait()

        sys.exit(3)

    def terminate(self):
        pass


reloader_loops = {
    'hachiko': HachikoReloaderLoop
}


reloader_loops['auto'] = reloader_loops['hachiko']


def run_with_reloader(main_func, extra_files=None, interval=1,
                      reloader_type='auto', loop=None):

    loop = loop or asyncio.get_event_loop()

    reloader = reloader_loops[reloader_type](extra_files, interval, loop=loop)

    import signal
    loop.add_signal_handler(signal.SIGTERM, lambda *args: loop.stop())
    try:
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            main_func(loop=loop)
            loop.run_until_complete(reloader.run())
        else:
            resultcode = loop.run_until_complete(reloader.restart_with_reloader())
            sys.exit(resultcode)
    except KeyboardInterrupt:
        pass
