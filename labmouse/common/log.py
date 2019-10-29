from labmouse.sproutlib.sproutlib import SproutSchema
import logging


class LogHelper(SproutSchema):
    class logger(SproutSchema):
        type = logging.RootLogger
        strict = False
        hidden = True

    class name(SproutSchema):
        '''
        The logger name.
        '''
        required = True

    class console(SproutSchema):
        '''
        Defaults to False since Unset is False by nature. Determines whether
        or not we log to console.
        '''
        type = bool

    class path(SproutSchema):
        '''
        The fully qualified path to the log file.
        '''
        pass

    class format(SproutSchema):
        '''
        The default format for all channels.
        '''
        pass

    class format_file(SproutSchema):
        '''
        A specific format for the file channel.
        '''
        pass

    class format_console(SproutSchema):
        '''
        A specific format for the console channel.
        '''
        pass

    class level(SproutSchema):
        '''
        The log level for all channels.
        '''
        pass

    class level_file(SproutSchema):
        '''
        Log level for the file channel.
        '''
        pass

    class level_console(SproutSchema):
        '''
        Log level for the console channel.
        '''
        pass

    DEFAULT_FORMAT = '%(asctime)s | %(levelname)s | %(message)s'
    DEFAULT_LEVEL = logging.DEBUG

    def __init__(self, *args, **kwargs):
        SproutSchema.__init__(self, *args, **kwargs)

        self.handlers = []

        L = logging.getLogger(self[self.name])

        # Set a default log level and let the user override it.
        v = self.DEFAULT_LEVEL
        if self.level in self:
            v = self.__string_to_level(self[self.level])

        # Set a default format and let the user override it.
        fmt = self.DEFAULT_FORMAT
        if self.format in self:
            fmt = self[self.format]

        # Generate the file handler and its params only if the path was set. If
        # it was not set, presume logging to file isn't desired.
        if self.path in self:
            h = logging.FileHandler(self[self.path])

            # Override formatting if the user requires it.
            if self.format_file in self:
                f = logging.Formatter(self[self.format_file])
            else:
                f = logging.Formatter(fmt)

            # Override the level if the user requests it.
            if self.level_file in self:
                v = self.__string_to_level(self[self.level_file])

            h.setFormatter(f)
            h.setLevel(v)

            L.addHandler(h)
            self.handlers += [h.stream]

        # Only log to console if the user wants it. Default is No.
        if self.console in self and self[self.console] is True:
            h = logging.StreamHandler()

            # Override formatting if the user requires it.
            if self.format_console in self:
                f = logging.Formatter(self[self.format_console])
            else:
                f = logging.Formatter(fmt)

            # Override the level if the user requests it.
            if self.level_console in self:
                v = self.__string_to_level(self[self.level_console])

            h.setFormatter(f)
            h.setLevel(v)

            L.addHandler(h)
            self.handlers += [h.stream]

        # If the generic level isn't set, then the logger won't engage.
        L.setLevel(v)

        self.__logger = L
        self[self.logger] = L

    def __string_to_level(self, _S):
        S = _S.upper()

        if S == "DEBUG":
            L = logging.DEBUG
        elif S == "INFO":
            L = logging.INFO
        elif S == "WARNING":
            L = logging.WARNING
        elif S == "ERROR":
            L = logging.ERROR
        elif S == "CRITICAL":
            L = logging.CRITICAL
        else:
            raise Exception("error: unsupported logging level {}".format(_S))

        return L
