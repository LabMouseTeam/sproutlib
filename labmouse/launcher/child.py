'''
This module represents a Child object and its importation.
'''
from importlib import import_module as importlib_import_module
from threading import Event as threading_Event
from sys import modules as sys_modules

from labmouse.sproutlib.sproutlib import SproutSchema


class Child(SproutSchema):
    '''
    A container representing the parameters for managing the sub-executable.
    '''
    class library_path(SproutSchema):
        '''
        The FQP of the Python3 library.
        '''
        required = True
        strict = True

    class module(SproutSchema):
        '''
        The Python module at the library path.
        '''
        required = True
        strict = True

    class class_name(SproutSchema):
        '''
        The class to load from the module at the library path.
        '''
        required = True
        strict = True

    class config(SproutSchema):
        '''
        This is the FQP to the YAML configuration file. It should be
        accessible outside of the sandbox and is opened prior to entering
        the sandbox.
        '''
        required = True
        strict = True

    def __init__(self, *args, **kwargs):
        SproutSchema.__init__(self, *args, **kwargs)

        self.inner_creator = None
        self.inner_name = ''

        self.__config = None
        self.__event = None

    def do_import(self):
        '''
        Perform the actual importation of a target object.
        '''
        # First, load the configuration file and make sure it is sane.
        f = open(self[self.config], 'r')
        self.__config = f.read()

        # Now, load the child object type in preparation for switching context.
        p = "{0}.{1}".format(self[self.library_path], self[self.module])

        self.logger.debug(
            'child: loading child: {0}.{1}'.format(p, self[self.class_name]))

        try:
            importlib_import_module(p)
            X = getattr(sys_modules[p], self[self.class_name])
        except Exception as E:
            # print('cant import: {}'.format(E))
            self.logger.error('child: unable to import module/class: {0}.{1}'
                .format(p, self[self.class_name]))
            raise E

        if X is None:
            self.logger.error('child: unknown load error; Leader is None')
            raise Exception('child: Leader is None')

        self.inner_creator = X
        self.inner_name = X.__name__

        self.__event = threading_Event()
        self.__event.clear()

    def new(self, timeout):
        '''
        Generate a new Child object.
        '''
        self.__event.clear()

        try:
            C = self.inner_creator(timeout, self.__event, self.__config)
            C.start()

        except Exception as E:
            self.logger.error('child: instantiation failed: {}'.format(E))
            raise E

        return C

    def clear(self):
        '''
        Clear the Child's Event state.
        '''
        self.__event.clear()
