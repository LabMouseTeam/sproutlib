# Copyright 2019 Lab Mouse, Inc. All Rights Reserved.
'''
Sproutlib is a library focused on turning standard Python 3 classes into
dynamic microservice objects from YAML. For more information, please see
the README.md file.
'''
import json

from random import getrandbits as random_getrandbits

from inspect import getmembers as inspect_getmembers
from inspect import isclass as inspect_isclass

from copy import deepcopy as copy_deepcopy
from copy import copy as copy_copy
from time import time as time_time
from math import modf as math_modf
from threading import Lock

from yaml.parser import ParserError as YAMLParserError
from yaml import safe_load as yaml_safe_load


class SproutStrictTypeException(Exception):
    '''
    This is simply a container for using a named (not generic) Exception.
    '''
    pass


class SproutNoSuchAttributeException(Exception):
    '''
    This exception is used when an object is created that contains keys which
    are not valid within the top-level object's name space. For example, if
    the object:
        class Foo(SproutSchema):
            class bar(SproutSchema):
                pass

    is created using the following YAML
        bar: 'i am a bar'
        baz: 'i am a baz'

    The key 'baz' should raise this exception, as no such key exists within
    the namespace 'Foo'.
    '''
    pass


class SproutBadStateException(Exception):
    '''
    This exception is raised when Sproutlib gets in a state that should never
    occur in the real world. For example, when a lock that never times out
    cannot actually return in a locked state. This should never happen, but
    we check, anyway.
    '''
    pass


class SproutIdentityException(Exception):
    '''
    This exception is raised when the internal identity map that ensures each
    SproutSchema is unique, even if copied or deepcopied, identifies collision
    during identity generation. This should never happen in the real world,
    but we check for it, anyway.
    '''
    pass


class SproutSchema(dict):
    '''
    This is a docstring to appease pylint. Fuck you, pylint.
    '''
    required = False
    strict = False
    hidden = False
    subtype = None
    type = str

    __BUILTIN__ = [
        bytes,
        float,
        str,
        int,
        bool,
        dict,
        tuple,
        object,
        list,
        ]

    identity_lock = Lock()
    identities = {}

    logger_lock = Lock()
    logger = None

    def _getmembers(self):
        x = inspect_getmembers(self.__class__, lambda a: SproutSchema._find(a))
        return [i[1] for i in x]

    @staticmethod
    def _find(a):
        if not inspect_isclass(a):
            return False

        if issubclass(a, SproutSchema):
            return True

        return False

    @staticmethod
    def __generate_hash():
        b = random_getrandbits(64)
        c = random_getrandbits(16)

        t = time_time()

        # Use the entropic fraction.
        f = math_modf(t)[0]
        e = int(f * 1000000)

        x = (c << 32) | e
        return b ^ x

    @classmethod
    def add_logger(cls, x):
        '''
        Use a class based logger (which is inherently a thread safe object)
        so each SproutSchema can use it without having to pass the object
        around or create duplicates.

        This function should be called by the top level SproutSchema to
        immediately make the logger available to subs that expect one.
        '''
        if cls.logger_lock.acquire() is not True:
            raise SproutBadStateException(
                'SproutSchame.add_logger: unexpected lock state')

        if cls.logger is None:
            cls.logger = x

        cls.logger_lock.release()

    @classmethod
    def __add_identity(cls, i):
        if cls.identity_lock.acquire() is not True:
            raise SproutBadStateException(
                'SproutSchema.__add_identity: unexpected lock state')

        if i in cls.identities:
            cls.identity_lock.release()
            raise SproutIdentityException(
                'SproutSchema.__add_identity: identity exists')

        cls.identities[i] = True
        cls.identity_lock.release()

    def __init__(self, *args, **kw):
        # Init the dict with nothing in it.
        dict.__init__(self, (), **kw)

        self.__iter_i = 0
        self.__iter_l = []

        self.__hash = self.__generate_hash()
        SproutSchema.__add_identity(self.__hash)

        # If we were loaded with a dict, process each name by class.
        if len(args) == 0:
            return

        # If we were seeded with a string, presume it's either YAML or JSON,
        # and parse it into an object.
        if len(args) == 1 and isinstance(args[0], str):
            try:
                a = json.loads(args[0])
            except json.JSONDecodeError:
                # If JSON didn't work, presume its YAML.
                try:
                    a = yaml_safe_load(args[0])
                except YAMLParserError as E:
                    raise E
        else:
            a = args[0]

        self.__do_update(a)

    def __del__(self):
        if SproutSchema.identity_lock.acquire() is not True:
            raise SproutBadStateException(
                'SproutSchema.__del__: can\'t lock on delete')

        try:
            SproutSchema.identities.pop(self.__hash)
        except KeyError:
            SproutSchema.identity_lock.release()
            raise SproutIdentityException(
                'SproutSchema.__del__: KeyError on delete for '
                '{}'.format(self.__hash))

        SproutSchema.identity_lock.release()

    def __do_update(self, d):
        for k in d.keys():
            # Try and resolve the class. If we can't do so, just fall-back to
            # the name.
            c = ''
            try:
                c = getattr(self, k)
            except AttributeError:
                c = k

            # Going to dict directly bypasses Strict etc
            self.__setitem__(c, d[k])

    def keys(self):
        # Only return keys that exist or are required.
        r = []
        m = self._getmembers()
        for i in m:
            if ((i not in self) and (i.required is True)) or (i in self):
                r += [i]

        return r

    def update(self, K):
        self.__do_update(K)

    def __iter__(self):
        """
        This does not return strings, so that the result can be useful to
        functions that would use classes as indicies.
        """
        self.__iter_l = self._getmembers()
        self.__iter_i = 0

        while self.__iter_i < len(self.__iter_l):
            k = self.__iter_l[self.__iter_i]
            self.__iter_i += 1
            if k.hidden is True:
                continue

            # Feign an object.
            if k not in self and k.required is True:
                yield (k, k.type())
            elif k in self:
                yield (k, self[k])

    def __test_strict2(self, k, _v, _t):
        if k.strict is True and not isinstance(_v, _t):
            raise SproutStrictTypeException(
                "SproutRoot.set: strict ({0}!={1})".format(
                    _t,
                    type(_v)))

        # We can't recursively inspect a dict, list, or tuple, because we
        # cannot accurately describe what should be in each facet of that
        # object. This works for lists at the top level, but not for lists as a
        # sub. A list as the type just means that there is a list, but does not
        # require the sub (facets of the list) to be a specific thing. This is
        # what the `subtype' clause is meant for, but that only describes one
        # level down. We can't go further with simple container types.

        # If the type is a SproutSchema container, recurse
        if issubclass(k.type, SproutSchema) is True:
            for i in _v.items():
                x = getattr(k, i[0], None)
                if x is None:
                    raise SproutNoSuchAttributeException(
                        "SproutRoot.set: no object '{0}' in "
                        "namespace {1}".format(
                            i[0],
                            k))

                if issubclass(x.type, SproutSchema) is not True:
                    if x.strict is not True:
                        continue

                    if isinstance(i[1], x.type) is not True:
                        raise SproutStrictTypeException(
                            "SproutRoot.set: strict obj={2}['{3}'] "
                            "types=({0}!={1})".format(
                                type(i[1]),
                                x.type,
                                k,
                                i[0]))
                else:
                    # Recurse to get all subs
                    self.__test_strict2(x, i[1], None)

    def __string_to_schema(self, k):
        for i in self._getmembers():
            if i.__name__ == k:
                return i

        return None

    def __setitem__(self, _k, v):
        if isinstance(_k, str):
            k = self.__string_to_schema(_k)
        else:
            k = _k

        if k is None:
            raise SproutNoSuchAttributeException(
                'SproutRoot.set: no such attribute: {}'.format(_k))

        return self.__test_strict(k, v)

    def __test_strict(self, k, v):
        if k.strict is True or issubclass(k.type, SproutSchema) is True:
            _t = k.type
            _v = v

            # We only validate another level deep.
            # DONB update this to be recursive, if possible.
            if _t == list and k.subtype is not None:
                # First, make sure the list is a list.
                self.__test_strict2(k, v, list)

                # Now, ensure each facet of the list is valid.
                _t = k.subtype
                for i in v:
                    self.__test_strict2(k, i, _t)
            else:
                self.__test_strict2(k, _v, _t)

        return dict.__setitem__(self, k, v)

    def __getitem__(self, x):
        # Allow gets based on the name, if it exists
        if isinstance(x, str):
            x = self.__string_to_schema(x)

        # Handle custom types
        if (x in self) and (x.type not in self.__BUILTIN__):
            o = None
            st = x.subtype
            if (x.type == list) and ((st != list) and (st != tuple)):

                m = []
                for i in dict.__getitem__(self, x):
                    o = x.subtype

                    # If the object has an update method, use it.
                    up = getattr(o, 'update', None)
                    if (up is not None) and (o in self.__BUILTIN__):
                        o.update(i)
                    elif (up is not None) and (o not in self.__BUILTIN__):
                        o = o(i)
                    else:
                        o = i

                    m += [o]
                return m

            elif (x.type == list) and ((st == list) or (st == tuple)):
                return dict.__getitem__(self, x)

            else:
                # First, attempt to retrieve the existing instance from the
                # inner dictionary. Only if it doesn't exist do we create it.
                v = dict.__getitem__(self, x)
                if isinstance(v, x.type) is True:
                    return v

                try:
                    o = x.type()
                    getattr(o, 'update')
                    o.update(v)
                except AttributeError:
                    o = x

                # If we created an object, set it.
                dict.__setitem__(self, x, o)
                return o

        elif (x not in self) and (x.required is True):
            v = x.type()
            # Set the value so that we have a base type.
            dict.__setitem__(self, x, v)
            return v

        # If the type is a builtin, just return the value
        return dict.__getitem__(self, x)

    def __repr__(self):
        # We have to override repr or it will leak keys not in KEYS. And
        # frankly, I don't care about the single-quote versus double-quote
        # regression. If we see this as a problem in the future, we'll fix it.
        return self.__str__()

    def items(self):
        x = dict.items(self)

        # Don't let items() ruin transitions from normal models to Shorts
        d = []
        for i in x:
            if i[0] not in self:
                continue
            d += [i]

        return d

    def __hash__(self):
        # We get straight to the point here by ensuring each hash is unique and
        # deliberately generated to represent this specific object, even it has
        # been deepcopied. This way, we can ensure correct object retrieval
        # from a dictionary (or any other hash use) without traversing what can
        # be a very complex recursive tree of namespaces.
        return hash(self.__hash)

    def __str__(self):
        d = {}
        for i in self:
            # __iter__ should always return the set of attributes based on the
            # SproutSchema class.
            i = i[0]

            # We ignore the required attribute and skip an object if it is
            # contained within this list. This is to ensure the name doesn't
            # appear in strings at all; i.e. internal objects only.
            if i.hidden is True:
                continue

            # If the type is required then generate a default value regardless
            # of whether or not it was defined by the writer.
            q = i.required
            t = i.type

            if i in self:
                d[i.__name__] = self[i]
            elif q is True:
                d[i.__name__] = t()

        return self.__json_dumps(d)

    def __json_dumps(self, d):
        if isinstance(d, dict):
            return self.__json_dict(d)
        elif isinstance(d, list):
            return self.__json_list(d)
        elif isinstance(d, tuple):
            return self.__json_list(d)

    def __json_dict(self, d):
        s = []
        for k in d.keys():
            v = d[k]

            # If the key isn't a string, use the class name.
            if isinstance(k, str) is not True and issubclass(k, SproutSchema):
                k = k.__name__

            # If the object is iterable, get recursive.
            if (isinstance(v, list) or
                    isinstance(v, tuple) or
                    isinstance(v, dict)):
                v = self.__json_dumps(v)
                s += ["\"{0}\": {1}".format(k, v)]
            else:
                # If the object is a number, generate the proper value.
                if isinstance(v, int) or isinstance(v, float):
                    # Bool is a sub of int. Make json happy.
                    if isinstance(v, bool):
                        if v is True:
                            v = 'true'
                        else:
                            v = 'false'

                    s += ["\"{0}\": {1}".format(k, v)]
                else:
                    # Otherwise, the type should be str.
                    if isinstance(v, str):
                        s += ["\"{0}\": \"{1}\"".format(k, v)]
                    else:
                        # For anything not caught by the above expressions, we
                        # presume the child object(s) may have a specific way
                        # to pickle the non-standard data. All we do otherwise
                        # is stringify the data, which is probably not what you
                        # want, especially if this data needs to be bytes, for
                        # example, and it needs to be deserialized correctly on
                        # the other end of whatever you're talking to.
                        #
                        # The notable side-effect of this transparency is that
                        # the receiver of the data must known how to unpickle
                        # it. Presumably the designer of a protocol using this
                        # library would know this, but it's worth expressing
                        # here. We also cannot provide a callback to unpickle
                        # all string data because - obviously - that would
                        # create extreme latency for what would mostly be false
                        # positives. Plan on unpickling things before you use
                        # them.
                        #
                        # If, for example, an object needs to be a bytes
                        # object, but needs to be accepted as a pickled JSON
                        # string, the object should be set to 'strict = False'
                        # and changed to bytes once the object is instantiated.
                        try:
                            x = getattr(self, 'sproutpickle')
                            v = x(v)
                        except AttributeError:
                            pass

                        s += ["\"{0}\": \"{1}\"".format(k, v)]

        r = ",".join(s)

        return "{0}{1}{2}".format('{', r, '}')

    def __json_list(self, d):
        s = []
        for v in d:
            if (isinstance(v, list) or
                    isinstance(v, tuple) or
                    isinstance(v, dict)):
                v = self.__json_dumps(v)
                s += [v]
            else:
                if isinstance(v, int) or isinstance(v, float):
                    s += ["{0}".format(v)]
                else:
                    s += ["\"{0}\"".format(v)]

        r = ", ".join(s)

        return "[{0}]".format(r)

    def __eq__(self, x):
        if isinstance(x, SproutSchema) is not True:
            return False

        _x = str(x)
        _y = str(self)
        return _x == _y
