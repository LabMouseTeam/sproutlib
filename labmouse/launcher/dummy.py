'''
A simple example Child.
'''
from time import sleep as time_sleep

from labmouse.sproutlib.sproutlib import SproutSchema
from labmouse.launcher.leader import ThreadLeader


class Dummy(ThreadLeader):
    '''
    A Dummy Child
    '''
    class test(SproutSchema):
        '''
        A do-nothing variable.
        '''
        pass

    def main(self):
        '''
        main() is literally what it sounds like: the main function called by
        the Launcher subsystem. This is your Child's main() entry point.
        '''
        i = 0
        while self.interrupted is not True:
            # We have to check in before the timeout. The timeout value is
            # passed to the initializer and pong() and sleep() will manage this
            # on your behalf.
            self.pong()
            self.sleep()

            # XXX just a friendly hello
            self.logger.info('meep')

            i += 1
            if i == 4:
                #'''
                # endless loop test
                while True:
                    time_sleep(1)
                '''
                # Test crashing
                self.logger.info('oops ;-)')
                raise Exception('lol oops')
                '''
