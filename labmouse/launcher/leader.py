'''
The Leader of the pack.
'''
from threading import Thread
from threading import get_ident as threading_get_ident
from time import sleep as time_sleep

from labmouse.sproutlib.sproutlib import SproutSchema


class ThreadLeader(SproutSchema, Thread):
    '''
    The Leader base class represents the parent class for all Children executed
    by the Launcher subsystem. All Children loaded into the Launcher should
    inherit this class. It handles all core communication functionality between
    the parent Launcher and the Child.
    '''
    # What percentage of the original timeout should we actually sleep.
    SLEEP_SCALE = 0.33

    def __init__(self, timeout, event, *args, **kwargs):
        SproutSchema.__init__(self, *args, **kwargs)
        Thread.__init__(self)

        self.__timeout = timeout
        self.__event = event
        self.__id = -1

        # This is *required* because if the thread locks up and we can't
        # communicate with it, and our master attempts to exit(), we will run
        # forever waiting for the Thread to exit. With daemon set, this thread
        # will be terminated automatically when the process exits.
        self.daemon = True

        self.interrupted = False
        self.do_ping = False

    def getid(self):
        '''
        Return the Thread ID.
        '''
        return self.__id

    def ping(self):
        '''
        This function should only be used by the Launcher, to tell the Leader
        and its Child(ren) to pong.
        '''
        # Tell the loop to pong.
        self.do_ping = True

        # Wait for the pong for our desired time.
        r = self.__event.wait(self.__timeout)

        # Immediately clear the Event wait flag.
        self.__event.clear()

        return r

    def pong(self):
        '''
        Respond to a ping.
        '''
        if self.do_ping is not True:
            return

        self.do_ping = False
        self.__event.set()

    def sleep(self, timeout=None):
        '''
        This is the preferred way for a Leader thread (or its children) to
        sleep. We scale the timeout value by SLEEP_SCALE, which helps ensure
        that we wake up and process a Ping before the timeout occurs.
        '''
        t = (self.__timeout * self.SLEEP_SCALE) if timeout is None else timeout
        time_sleep(t)

    def join(self, timeout=None):
        '''
        Join a thread the kind way.
        '''
        self.interrupted = True

        t = timeout if timeout is not None else self.__timeout
        Thread.join(self, timeout=t)

    def run(self):
        '''
        Execute the Child's main function.
        '''
        # We have to do this from within our context.
        self.__id = threading_get_ident()

        self.main()

        self.logger.debug('leader: child has exited!')
