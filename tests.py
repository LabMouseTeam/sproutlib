from labmouse.sproutlib.Sproutlib import SproutRoot, SproutSchema
import unittest
import base64
import json
import sys


class TestInheritance(unittest.TestCase):
    '''
    Test object inheritance for SproutSchema.
    '''
    class Foo(SproutRoot):
        class f1(SproutSchema):
            pass

        class f2(SproutSchema):
            required = True

        class f3(SproutSchema):
            required = True
            type = int

        class f4(SproutSchema):
            required = True
            type = list

    class Bar(Foo):
        class b1(SproutSchema):
            required = True

    class Baz(Bar):
        class b2(SproutSchema):
            pass

    def test_basic(self):
        '''
        Test multiple levels of inheritance to ensure that the objects can be
        configured automatically.
        '''
        y = """
            # All objects are top level in the hierarchy
            b1: 'b1'
            b2: 'i am b2'
            f1: 'f1'
            f2: 'i am f2'
            f3: 127
            f4:
                - 1
                - 2
                - 3
            """

        b = self.Baz(y)

        if b[b.b1] != 'b1':
            raise Exception('inheritance1 failure')
        if b[b.b2] != 'i am b2':
            raise Exception('inheritance1 failure')
        if b[b.f1] != 'f1':
            raise Exception('inheritance1 failure')
        if b[b.f2] != 'i am f2':
            raise Exception('inheritance1 failure')
        if b[b.f3] != 127:
            raise Exception('inheritance1 failure')
        if b[b.f4] != [1, 2, 3]:
            raise Exception('inheritance1 failure')

        if b['b1'] != 'b1':
            raise Exception('inheritance1 failure')
        if b['b2'] != 'i am b2':
            raise Exception('inheritance1 failure')
        if b['f1'] != 'f1':
            raise Exception('inheritance1 failure')
        if b['f2'] != 'i am f2':
            raise Exception('inheritance1 failure')
        if b['f3'] != 127:
            raise Exception('inheritance1 failure')
        if b['f4'] != [1, 2, 3]:
            raise Exception('inheritance1 failure')


class TestObject(unittest.TestCase):
    '''
    Test the python float type.
    '''
    def test_unpickle(self):
        '''
        Ensure we can unpickle data without raising an exception.
        '''
        class Bar(object):
            def __init__(self):
                self.baz = 'i am a baz'
                self.buu = 128

            def __eq__(self, x):
                return self.baz == x.baz and self.buu == x.buu


        class Foo(SproutRoot):
            class object1(SproutSchema):
                required = True
                type = object

            def sproutpickle(self, x):
                if isinstance(x, Bar):
                    d = {'baz': x.baz, 'buu': x.buu}
                    return json.dumps(d)

            def unpickle_all(self):
                o = self[self.object1]
                b = Bar()

                b.baz = o['baz']
                b.buu -= o['buu']

                self[self.object1] = b

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()


        S = '{"object1": {"baz": "testme", "buu": 1}}'
        f = Foo(S)

        b1 = Bar()
        b1.baz = 'testme'
        b1.buu -= 1

        b2 = Bar()
        b2.baz = 'testyou'
        b2.buu += 1

        x = f[f.object1]

        if b1 != x:
            raise Exception('error: object1 mismatch')

        if b2 == x:
            raise Exception('error: object1 shouldnt match')

    def test_basic(self):
        '''
        Just make sure the data is stored correctly and is retrievable via its
        name and its object.
        '''
        class Bar(object):
            def __init__(self):
                self.baz = 'i am a baz'
                self.buu = 128

            def __eq__(self, x):
                return self.baz == x.baz and self.buu == x.buu

            def __repr__(self):
                d = {'baz': self.baz, 'buu': self.buu}
                return json.dumps(d)


        class Foo(SproutRoot):
            class object1(SproutSchema):
                required = True
                type = object
                strict = False

            def sproutpickle(self, x):
                if isinstance(x, Bar):
                    d = {'baz': x.baz, 'buu': x.buu}
                    return json.dumps(d)

            def unpickle_all(self):
                o = self[self.object1]
                b = Bar()

                b.baz = o['baz']
                b.buu -= o['buu']

                self[self.object1] = b

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()


        b1 = Bar()
        b2 = Bar()

        f = Foo({'object1': {'baz': 'i am a baz', 'buu': 0}})

        # Retrieve by name.
        if f['object1'] != b2:
            raise Exception('error: get-by-name fails on object1')

        # Retrieve by object.
        if f[f.object1] != b2:
            raise Exception('error: get-by-obj fails on object1')

        d = Bar()
        d2 = {'object1': str(d)}
        s0 = json.dumps(d2)
        s = str(f)

        # Ensure the JSON string is valid.
        if s != s0.replace('\\', ''):
            raise Exception('error: str mismatch on float1')


class TestList(unittest.TestCase):
    '''
    Test the python float type.
    '''
    def test_unpickle(self):
        '''
        Ensure we can unpickle data without raising an exception.
        '''
        class Foo(SproutRoot):
            class list1(SproutSchema):
                required = True
                type = list

            def unpickle_all(self):
                # We shouldn't need pickling for a simple type.
                pass

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()

        b1 = [1, "two", 3]
        S = '{"list1": '
        S += '{}'.format(b1)
        S += '}'
        f = Foo(S)

        if b1 != f[f.list1]:
            raise Exception('list1 mismatch')

    def test_basic(self):
        '''
        Just make sure the data is stored correctly and is retrievable via its
        name and its object.
        '''
        class Foo(SproutRoot):
            def sproutpickle(self, x):
                return base64.b64encode(x).decode('utf-8')

            class list1(SproutSchema):
                required = True
                type = list

        b1 = [1, "two", 3]
        b2 = [1, "two", 3]
        f = Foo({'list1': b1})

        # Retrieve by name.
        if f['list1'] != b2:
            raise Exception('error: get-by-name fails on list1')

        # Retrieve by object.
        if f[f.list1] != b2:
            raise Exception('error: get-by-obj fails on list1')

        d = {'list1': b1}
        s0 = json.dumps(d)
        s = str(f)

        # Ensure the JSON string is valid.
        if s != s0.replace('\'', '"'):
            raise Exception('error: str mismatch on list1')


class TestTuple(unittest.TestCase):
    '''
    Test the python float type.
    '''
    def test_unpickle(self):
        '''
        Ensure we can unpickle data without raising an exception.
        '''
        class Foo(SproutRoot):
            class tuple1(SproutSchema):
                required = True
                type = tuple

            def unpickle_all(self):
                # JSON doesn't process tuples so we need to unpickle
                if self.tuple1 in self and isinstance(self[self.tuple1], list):
                    self[self.tuple1] = tuple(self[self.tuple1])

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()

        b1 = (1, "two", 3)
        S = '{"tuple1": '
        S += '{}'.format(list(b1))
        S += '}'
        f = Foo(S)

        if b1 != f[f.tuple1]:
            raise Exception('tuple1 mismatch')

    def test_basic(self):
        '''
        Just make sure the data is stored correctly and is retrievable via its
        name and its object.
        '''
        class Foo(SproutRoot):
            def sproutpickle(self, x):
                return base64.b64encode(x).decode('utf-8')

            class tuple1(SproutSchema):
                required = True
                type = tuple

        b1 = (1, "two", 3)
        b2 = (1, "two", 3)
        f = Foo({'tuple1': b1})

        # Retrieve by name.
        if f['tuple1'] != b2:
            raise Exception('error: get-by-name fails on tuple1')

        # Retrieve by object.
        if f[f.tuple1] != b2:
            raise Exception('error: get-by-obj fails on tuple1')

        d = {'tuple1': b1}
        s0 = json.dumps(d)
        s = str(f)

        # Ensure the JSON string is valid.
        if s != s0.replace('\'', '"'):
            raise Exception('error: str mismatch on tuple1')


class TestDict(unittest.TestCase):
    '''
    Test the python float type.
    '''
    def test_unpickle(self):
        '''
        Ensure we can unpickle data without raising an exception.
        '''
        class Foo(SproutRoot):
            class dict1(SproutSchema):
                required = True
                type = dict

            def unpickle_all(self):
                # We shouldn't need pickling for a simple type.
                pass

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()

        b1 = {'sub1': {'sub2': {'sub3': 3}}}
        S = """{"dict1": """
        S += "{}".format(b1)
        S += "}"
        f = Foo(S)

        if b1 != f[f.dict1]:
            raise Exception('dict1 mismatch')

    def test_basic(self):
        '''
        Just make sure the data is stored correctly and is retrievable via its
        name and its object.
        '''
        class Foo(SproutRoot):
            def sproutpickle(self, x):
                return base64.b64encode(x).decode('utf-8')

            class dict1(SproutSchema):
                required = True
                type = dict

        b1 = {'sub1': {'sub2': {'sub3': 3}}}
        b2 = {'sub1': {'sub2': {'sub3': 3}}}
        f = Foo({'dict1': b1})

        # Retrieve by name.
        if f['dict1'] != b2:
            raise Exception('error: get-by-name fails on dict1')

        # Retrieve by object.
        if f[f.dict1] != b2:
            raise Exception('error: get-by-obj fails on dict1')

        d = {'dict1': b1}
        s0 = str(d)
        s = str(f)

        # Ensure the JSON string is valid.
        if s != s0.replace('\'', '"'):
            raise Exception('error: str mismatch on dict1')


class TestBool(unittest.TestCase):
    '''
    Test the python float type.
    '''
    def test_unpickle(self):
        '''
        Ensure we can unpickle data without raising an exception.
        '''
        class Foo(SproutRoot):
            class bool1(SproutSchema):
                required = True
                type = bool

            def unpickle_all(self):
                # We shouldn't need pickling for a simple type.
                pass

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()

        b1 = True
        f = Foo("""{"bool1": true}""")

        if b1 != f[f.bool1]:
            raise Exception('bool1 mismatch')

    def test_basic(self):
        '''
        Just make sure the data is stored correctly and is retrievable via its
        name and its object.
        '''
        class Foo(SproutRoot):
            def sproutpickle(self, x):
                return base64.b64encode(x).decode('utf-8')

            class bool1(SproutSchema):
                required = True
                type = bool

        b1 = True
        b2 = True
        f = Foo({'bool1': b1})

        # Retrieve by name.
        if f['bool1'] != b2:
            raise Exception('error: get-by-name fails on bool1')

        # Retrieve by object.
        if f[f.bool1] != b2:
            raise Exception('error: get-by-obj fails on bool1')

        d = {'bool1': True}
        s0 = str(d)
        s = str(f)

        # Ensure the JSON string is valid.
        if s != s0.replace('\'', '"').replace('T', 't'):
            raise Exception('error: str mismatch on bool1')


class TestInt(unittest.TestCase):
    '''
    Test the python float type.
    '''
    def test_unpickle(self):
        '''
        Ensure we can unpickle data without raising an exception.
        '''
        class Foo(SproutRoot):
            class int1(SproutSchema):
                required = True
                type = int

            def unpickle_all(self):
                # We shouldn't need pickling for a simple type.
                pass

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()

        b1 = 127
        f = Foo("""{"int1": 127}""")

        if b1 != f[f.int1]:
            raise Exception('int1 mismatch')

    def test_basic(self):
        '''
        Just make sure the data is stored correctly and is retrievable via its
        name and its object.
        '''
        class Foo(SproutRoot):
            def sproutpickle(self, x):
                return base64.b64encode(x).decode('utf-8')

            class int1(SproutSchema):
                required = True
                type = int

        b1 = 127
        b2 = 127
        f = Foo({'int1': b1})

        # Retrieve by name.
        if f['int1'] != b2:
            raise Exception('error: get-by-name fails on int1')

        # Retrieve by object.
        if f[f.int1] != b2:
            raise Exception('error: get-by-obj fails on int1')

        d = {'int1': 127}
        s0 = str(d)
        s = str(f)

        # Ensure the JSON string is valid.
        if s != s0.replace('\'', '"'):
            raise Exception('error: str mismatch on int1')


class TestStr(unittest.TestCase):
    '''
    Test the python float type.
    '''
    def test_unpickle(self):
        '''
        Ensure we can unpickle data without raising an exception.
        '''
        class Foo(SproutRoot):
            class str1(SproutSchema):
                required = True

            def unpickle_all(self):
                # We shouldn't need pickling for a simple type.
                pass

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()

        b1 = "the quick brown fox posts pointlessly on reddit"
        S = '{"str1": '
        S += '{}'.format(b1)
        S += '}'
        f = Foo(S)

        if b1 != f[f.str1]:
            raise Exception('str1 mismatch')

    def test_basic(self):
        '''
        Just make sure the data is stored correctly and is retrievable via its
        name and its object.
        '''
        class Foo(SproutRoot):
            def sproutpickle(self, x):
                return base64.b64encode(x).decode('utf-8')

            class str1(SproutSchema):
                required = True

        b1 = "the quick brown fox posts pointlessly on reddit"
        b2 = "the quick brown fox posts pointlessly on reddit"
        f = Foo({'str1': b1})

        # Retrieve by name.
        if f['str1'] != b2:
            raise Exception('error: get-by-name fails on float1')

        # Retrieve by object.
        if f[f.str1] != b2:
            raise Exception('error: get-by-obj fails on float1')

        d = {'str1': b1}
        s0 = str(d)
        s = str(f)

        # Ensure the JSON string is valid.
        if s != s0.replace('\'', '"'):
            raise Exception('error: str mismatch on str1')


class TestFloat(unittest.TestCase):
    '''
    Test the python float type.
    '''
    def test_unpickle(self):
        '''
        Ensure we can unpickle data without raising an exception.
        '''
        class Foo(SproutRoot):
            class float1(SproutSchema):
                required = True
                type = float

            def unpickle_all(self):
                # We shouldn't need pickling for a simple type.
                pass

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()

        b1 = 0.127
        f = Foo("""{"float1": 0.127}""")

        if b1 != f[f.float1]:
            raise Exception('float1 mismatch')

    def test_basic(self):
        '''
        Just make sure the data is stored correctly and is retrievable via its
        name and its object.
        '''
        class Foo(SproutRoot):
            def sproutpickle(self, x):
                return base64.b64encode(x).decode('utf-8')

            class float1(SproutSchema):
                required = True
                type = float

        b1 = 0.127
        b2 = 0.127
        f = Foo({'float1': b1})

        # Retrieve by name.
        if f['float1'] != b2:
            raise Exception('error: get-by-name fails on float1')

        # Retrieve by object.
        if f[f.float1] != b2:
            raise Exception('error: get-by-obj fails on float1')

        d = {'float1': 0.127}
        s0 = str(d)
        s = str(f)

        # Ensure the JSON string is valid.
        if s != s0.replace('\'', '"'):
            raise Exception('error: str mismatch on float1')


class TestBytes(unittest.TestCase):
    '''
    Test the python bytes type.
    '''

    def test_unpickle(self):
        '''
        Ensure we can unpickle data without raising an exception.
        '''
        class Foo(SproutRoot):
            class bytes1(SproutSchema):
                required = True
                type = str
                strict = False

            def unpickle_all(self):
                if self.bytes1 in self:
                    self[self.bytes1] = base64.b64decode(self[self.bytes1])

            def __init__(self, *args, **kwargs):
                SproutRoot.__init__(self, *args, **kwargs)
                self.unpickle_all()

        b1 = b'\x11\x22\x33\x44\x55'

        f = Foo("""{"bytes1": "ESIzRFU="}""")

        if b1 != f[f.bytes1]:
            raise Exception('bytes1 mismatch')

    def test_basic(self):
        '''
        Just make sure the data is stored correctly and is retrievable via its
        name and its object.
        '''
        class Foo(SproutRoot):
            def sproutpickle(self, x):
                return base64.b64encode(x).decode('utf-8')

            class bytes1(SproutSchema):
                required = True
                type = bytes

        b1 = b'\x11\x22\x33\x44\x55'
        b2 = b'\x11\x22\x33\x44\x55'
        f = Foo({'bytes1': b1})

        # Retrieve by name.
        if f['bytes1'] != b2:
            raise Exception('error: get-by-name fails on bytes1')

        # Retrieve by object.
        if f[f.bytes1] != b2:
            raise Exception('error: get-by-obj fails on bytes1')

        d = {'bytes1': "ESIzRFU="}
        s0 = str(d)
        s = str(f)

        # Ensure the JSON string is valid.
        if s != s0.replace('\'', '"'):
            raise Exception('error: str mismatch on bytes1')


if __name__ == "__main__":
    unittest.main()
