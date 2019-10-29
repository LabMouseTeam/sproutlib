'''
Objects corresponding to a sandbox (chroot).
'''
from labmouse.sproutlib.sproutlib import SproutSchema


class Sandbox(SproutSchema):
    '''
    Define the parameters we need to know to properly enter a secure sandbox.
    '''

    class detach(SproutSchema):
        '''
        Should the child process detach itself (daemonize) from the parent?
        '''
        required = True
        strict = True
        type = bool

    class working_directory(SproutSchema):
        '''
        The starting working directory for the daemon from within the chroot.
        '''
        required = True
        strict = True

    class chroot_directory(SproutSchema):
        '''
        Fully qualified path to the root of the sandbox on the host.
        '''
        required = True
        strict = True

    class umask(SproutSchema):
        '''
        Starting umask.
        '''
        required = True
        strict = True
        type = int

    class uid(SproutSchema):
        '''
        Child process UID.
        '''
        required = True
        strict = True
        type = int

    class gid(SproutSchema):
        '''
        Child process GID.
        '''
        required = True
        strict = True
        type = int
