'''
Generic container for the Launcher subsystem.
'''
import os
import time

from threading import enumerate as threading_enumerate

from labmouse.sproutlib.sproutlib import SproutSchema
from labmouse.launcher.launcher import Launcher


class ProcessLauncher(SproutSchema):
    '''
    Next generation Thread Launcher.
    '''
    class launcher(Launcher):
        '''
        The internal Launcher that does the real work.
        '''
        type = Launcher
        strict = False

    class tz(SproutSchema):
        '''
        A string denoting the preferred timezone.
        '''
        required = False
        strict = True

    def __init__(self, loghelper, *args, **kwargs):
        SproutSchema.__init__(self, *args, **kwargs)

        # This must be the LogHelper
        SproutSchema.add_logger(loghelper[loghelper.logger])
        # A lot of nonsense to get access to streams.
        self.loghandlers = loghelper.handlers

        # Always set the time zone to UTC by default.
        if self.tz in self:
            os.environ['TZ'] = self[self.tz]
        else:
            os.environ['TZ'] = 'UTC'
        time.tzset()

        # Defaults
        self.interrupted = False

    def start(self):
        '''
        Import and launch the target Child object.
        '''
        L = self[self.launcher]

        # Import the child prior to migrating into the sandbox, which helps
        # ensure that we don't need to do dynamic loading within the sandbox,
        # itself.
        L.do_import()

        # Switch us to the daemon context.
        L.daemonize(self.loghandlers)

        # Run the child within the daemon context.
        L.run()

        self.logger.debug(
            'exiting; threads alive={}'.format(len(threading_enumerate())))
