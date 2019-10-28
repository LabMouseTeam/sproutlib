'''
This module launches a child process and manages its execution, ensuring that
the child is stable and healthy. This module will restart the child based on
options similar to Erlang's supervisor model.
'''
from sys import stdout as sys_stdout
from sys import stderr as sys_stderr

from signal import SIGTERM as signal_SIGTERM
from signal import SIGUSR1 as signal_SIGUSR1
from signal import SIGHUP as signal_SIGHUP
from signal import SIGINT as signal_SIGINT

from threading import enumerate as threading_enumerate

from labmouse.launcher.pidfile import PidFile
from labmouse.launcher.sandbox import Sandbox
from labmouse.launcher.child import Child

from labmouse.sproutlib.sproutlib import SproutSchema

from daemon import DaemonContext as daemon_DaemonContext


class Launcher(SproutSchema):
    '''
    A container for the sub-executable launcher and its context.
    '''

    STRATEGY_EXIT_IS_RESTART = 'exit_is_restart'
    STRATEGY_EXIT_IS_FAIL = 'exit_is_fail'
    STRATEGY_RESTART = 'restart'
    STRATEGY_FAIL = 'fail'
    STRATEGY_OK = 'ok'

    STATE_CONTINUE = 'continue'
    STATE_RETURN = 'return'

    class thread_ceiling(SproutSchema):
        '''
        This defines the number of Leader threads that can be spawned at one
        time. Exceeding this amount is an indication that the threads are
        locking up and not exiting. Since we can't technically kill the
        threads, they will keep consuming resources until a more drastic and
        unstable crash occurs. If we see the base thread total exceeding this
        amount, we should exit gracefully and presume the threads have
        crashed. While both cases result in volatility, we are attempting to
        reduce volatility and exit as controlled as possible.
        '''
        required = False
        strict = True
        type = int

    class strategy(SproutSchema):
        '''
        The strategy used to manage the sub-executable state.
        '''
        required = True
        strict = True

    class monitor_timeout(SproutSchema):
        '''
        The amount of time the monitor should wait for a heartbeat before
        declaring the sub-executable deceased or locked.
        '''
        required = True
        strict = True
        type = float

    class sandbox(Sandbox):
        '''
        The sandbox parameters for launching a process.
        '''
        required = True
        type = Sandbox

    class child(Child):
        '''
        The runnable child object.
        '''
        required = True
        type = Child

    class pidfile(PidFile):
        '''
        This is a PidFile that we open outside the sandbox.
        '''
        required = True
        type = PidFile

    def __init__(self, *args, **kwargs):
        SproutSchema.__init__(self, *args, **kwargs)

        self.custom_signal = False
        self.interrupted = False
        self.restart = False

    def do_import(self):
        '''
        Import the child object.
        '''
        self[self.child].do_import()

    def daemonize(self, loghandlers):
        '''
        Switch into a daemon context.
        '''
        self.logger.debug('launcher.deamonize: !')

        try:
            S = self[self.sandbox]

            with self[self.pidfile]:
                with daemon_DaemonContext(
                        detach_process=S[S.detach],
                        uid=S[S.uid],
                        gid=S[S.gid],
                        umask=S[S.umask],
                        chroot_directory=S[S.chroot_directory],
                        working_directory=S[S.working_directory],
                        files_preserve=[
                            # We don't need to preserve stdin/out if we pass
                            # them as "new" stderr/stdout options below.
                            #
                            # We *have* to preserve the pidfile because after
                            # DaemonContext "returns" we are still within the
                            # sandbox if one was defined, and any attempt to
                            # reopen the file will be within the box.
                            self[self.pidfile].pidfile,
                            # This is a pain but we have to do it.
                            # Note that pylint can't parse this lol.
                            *tuple(loghandlers)],
                        stdout=sys_stdout,
                        stderr=sys_stderr,
                        pidfile=None,
                        prevent_core=True,  # this should be explicit
                        signal_map={
                            signal_SIGTERM: self.signal_handler,
                            signal_SIGUSR1: self.signal_handler,
                            signal_SIGHUP: self.signal_handler,
                            signal_SIGINT: self.signal_handler}):
                    pass
        except Exception as E:
            self.logger.info('caught dameoncontext exception: {}'.format(E))
            raise E

    def is_ceiling(self):
        '''
        Check the thread ceiling and determine if we've hit it.
        '''
        C = self[self.thread_ceiling] if self.thread_ceiling in self else 0
        if C == 0:
            return False

        F = filter(
            lambda x: isinstance(x, self[self.child].inner_creator),
            threading_enumerate())

        return len(list(F)) >= C

    def run(self):
        '''
        The main runtime loop for managing the Child.
        '''
        while True:
            self.logger.debug('launcher: creating new child')

            # Ensure that we aren't amassing locked threads if we're restarting
            # too often.
            if self.is_ceiling() is True:
                self.logger.error('launcher: crashed thread ceiling; exiting')
                break

            # This is the restart loop. Whenever we hit the top of this loop,
            # we presume we are creating a new child and launching it. This
            # resets the Event subsystem and launches the child.
            c = self[self.child].new(self[self.monitor_timeout])

            self.logger.debug('launcher: child created: {}'.format(c.getid()))
            self.logger.debug('launcher: entering management loop')

            i = 0
            while True:
                i += 1

                # This is the management loop that monitors an active child.

                # XXX should probably check a for custom service requests such
                # as Firehose
                # if self.custom_signal == True:

                # Act on interrupts and hangups.
                if self.interrupted is True or self.restart is True:
                    self.logger.warning(
                        'launcher: signal; interrupt={0} restart={1}'.format(
                            self.interrupted,
                            self.restart))

                    c.join(timeout=self[self.monitor_timeout])
                    if c.is_alive() is True:
                        # With daemon=True set, these threads will exit once we
                        # decide we've hit the crash ceiling, so this is OK.
                        # But, we still need to warn the World.
                        self.logger.warning('launcher: child is still alive!')

                    if self.interrupted is True:
                        self.logger.info('launcher: child interrupted; exited')
                        return

                    self.restart = False
                    self.logger.info('launcher: restart request; restarting..')
                    break

                watchdog_failed = not c.ping()
                exited = not c.is_alive()

                # Is the child healthy?
                if watchdog_failed is True or exited is True:
                    # Nope.
                    pass
                else:
                    # Yes, it is.
                    continue

                # Decide how to handle the child's state based on our
                # management strategy. With an unhealthy child, we either
                # return and give up, or we break to restart the child.
                r = self.handle_child_state(watchdog_failed, exited)
                if r == self.STATE_RETURN:
                    # Strategy is to halt.
                    return

                # Our strategy is to restart.
                break

    def handle_child_state(self, watchdog_failed, exited):
        '''
        Handle child state when it seems that it has failed.
        '''
        S = self[self.strategy]

        if S == self.STRATEGY_OK:
            self.logger.info('launcher: child exited; strategy=ok')
            return self.STATE_RETURN

        elif S == self.STRATEGY_FAIL:
            if exited is True:
                self.logger.info(
                    'launcher: child exited; strategy=fail; shutting down')
            else:
                self.logger.error(
                    'launcher: watchdog failure; child mute; strategy=fail')

            return self.STATE_RETURN

        elif S == self.STRATEGY_EXIT_IS_FAIL:
            self.logger.error(
                'launcher: child gone; exited={}; '
                'strategy=exit_is_fail; shutting down'.format(exited))

            return self.STATE_RETURN

        elif S == self.STRATEGY_RESTART:
            # Restart the child in all cases (crash or graceful exit).
            if exited is True:
                self.logger.warning(
                    'launcher: child exited; strategy=restart; restarting...')
            else:
                # It's notable that there is no way to truly terminate the
                # child in this case, so if the Threads keep crashing and
                # locking up, eventually resources will be starved. This is a
                # dangerous method and probably shouldn't be used except in
                # testing.
                self.logger.warning(
                    'launcher: child zombie; strategy=restart; restarting...')

            return self.STATE_CONTINUE

        elif S == self.STRATEGY_EXIT_IS_RESTART:
            # In this case, a non-graceful exit does not result in a restart.
            if watchdog_failed is True and exited is not True:
                self.logger.error(
                    'launcher: watchdog failure; strategy=EIR; shutting down')
                return self.STATE_RETURN

            self.logger.info(
                'launcher: child gone; exited={}; restarting'.format(exited))
            return self.STATE_CONTINUE

        self.logger.error('launcher: handle_child_state: unknown state!')

        # Always fail if we reach this juncture.
        return self.STATE_RETURN

    def signal_handler(self, signo, _f):
        '''
        Simple signal handler.
        '''
        self.logger.debug('launcher: signal observed: signo={}'.format(signo))

        if signo == signal_SIGHUP:
            self.logger.debug('caught hangup')
            self.restart = True
        elif signo == signal_SIGUSR1:
            self.logger.debug('caught usr1')
            self.custom_signal = True
        else:
            self.logger.debug('caught intr')
            self.interrupted = True
