'''
A PidFile helper class.
'''
from os import getpid as os_getpid
from os import stat as os_stat

from labmouse.sproutlib.sproutlib import SproutSchema


class PidFile(SproutSchema):
    '''
    A note about PidFiles and python-daemon. The daemon library, at least at
    the time of writing this (2019), opens and closes the PidFile within the
    context of the daemonized process, which is ridiculous. So, if the proc is
    instantiated within a sandbox, the PidFile context will be entered within
    the sandbox.

    It is far more preferable to enter the PidFile context (open the and write
    the file) within the context of the parent process, outside of the
    sandbox. This can be easily done if this context is entered using a `with'
    statement prior to calling DaemonContext(). However, this comes with a
    catch.

    In both cases, the PidFile context is exited within the Daemon context,
    meaning that we only have access to the file descriptor from within the
    sandbox. This means that we cannot reopen the file, which - in Python -
    means we can't delete it. There is no way to unlink the file from a
    file descriptor without using the name.

    So, the best way we can deal with this dangling state is by truncating
    the value of the PidFile. Using this method, we can reasonably deal with
    both use cases (entering our context from within and outside of the
    sandbox).
    '''

    class path(SproutSchema):
        '''
        The path to the PID file (pre-sandbox).
        '''
        required = True
        strict = True

    def __init__(self, *args, **kwargs):
        SproutSchema.__init__(self, *args, **kwargs)

        # This needs to be exposed for DaemonContext.
        self.pidfile = None

    def __enter__(self):
        f = None
        s = None
        try:
            s = os_stat(self[self.path])
        except FileNotFoundError:
            pass
        else:
            if s.st_size != 0:
                raise Exception('pidfile: live pidfile: {}'.format(s.st_size))

        try:
            f = open(self[self.path], 'w')
        except Exception as E:
            self.logger.error('error: pidfile: {}'.format(E))
            raise E

        self.pidfile = f
        self.pidfile.write('{}'.format(os_getpid()))

    def __exit__(self, _a, _b, _c):
        try:
            f = self.pidfile
            f.seek(0, 0)
            f.truncate()
            f.close()
        except Exception as E:
            self.logger.error('pidfile: exception on truncate: {}'.format(E))
