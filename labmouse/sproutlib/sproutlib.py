'''
This is a docstring to appease pylint. Fuck you, pylint.
'''
import inspect
import json
import yaml


class SproutStrictTypeException(Exception):
    '''
    This is a docstring to appease pylint. Fuck you, pylint.
    '''
    pass


class SproutSchema(object):
    '''
    This is a docstring to appease pylint. Fuck you, pylint.
    '''
    required = False
    strict = True
    hidden = False
    subtype = None
    type = str


class SproutRoot(dict):
    '''
    This is a docstring to appease pylint. Fuck you, pylint.
    '''
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

    __iter_i = 0
    __iter_l = []

    def _getmembers(self):
        x = inspect.getmembers(self.__class__, lambda a: SproutRoot._find(a))
        return [i[1] for i in x]

    def _find(a):
        if not inspect.isclass(a):
            return False

        if issubclass(a, SproutSchema):
            return True

        return False

    def __init__(self, *args, **kw):
        # Init the dict with nothing in it.
        dict.__init__(self, (), **kw)

        # If we were loaded with a dict, process each name by class.
        if len(args) == 0:
            return

        # If we were seeded with a string, presume it's either YAML or JSON,
        # and parse it into an object.
        if len(args) == 1 and isinstance(args[0], str):
            try:
                a = json.loads(args[0])
            except Exception as E:
                # If JSON didn't work, presume its YAML.
                try:
                    a = yaml.safe_load(args[0])
                except Exception as E:
                    raise E
        else:
            a = args[0]

        self.__do_update(a)

    def __do_update(self, d):
        for k in d.keys():
            # Try and resolve the class. If we can't do so, just fall-back to
            # the name.
            c = ''
            try:
                c = getattr(self, k)
            except Exception:
                c = k

            dict.__setitem__(self, c, d[k])

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

    def __test_strict(self, _v, _t):
        if not isinstance(_v, _t):
            raise SproutStrictTypeException(
                "SproutRoot.set: strict ({0}!={1})".format(
                    _t,
                    type(_v)))

    def __string_to_schema(self, k):
        for i in self._getmembers():
            if i.__name__ == k:
                return i

        return None

    def __setitem__(self, k, v):
        if isinstance(k, str):
            k = self.__string_to_schema(k)

        if k.strict is True:
            _t = k.type
            _v = v

            # We only validate another level deep.
            # DONB update this to be recursive, if possible.
            if _t == list and k.subtype is not None:
                # First, make sure the list is a list.
                self.__test_strict(v, list)

                # Now, ensure each facet of the list is valid.
                _t = k.subtype
                for i in v:
                    self.__test_strict(i, _t)
            else:
                self.__test_strict(_v, _t)

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
                try:
                    o = x.type()
                    getattr(o, 'update')
                    o.update(dict.__getitem__(self, x))
                except AttributeError:
                    o = x
                return o

        elif (x not in self) and (x.required is True):
            return x.type()

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
        t = tuple(self.items())
        t2 = []
        for i in t:
            D1 = i[0]
            if isinstance(i[0], dict) or isinstance(i[0], list):
                D1 = json.dumps(i[0])

            D2 = i[1]
            if isinstance(i[1], dict) or isinstance(i[1], list):
                D2 = json.dumps(i[1])

            t2 += [(D1, D2)]

        return hash(tuple(t2))

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

    def className(self):
        '''
        DONB: I forgot why I needed this. Test and delete.
        '''
        return self.__class__.__name__

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
            if (isinstance(k, str) is not True) and issubclass(k, SproutSchema):
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
                        except Exception as E:
                            print('exception? {}'.format(E))
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