from labmouse.sproutlib.Sproutlib import SproutRoot, SproutSchema
import unittest
import base64
import sys


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
        f = Foo("""{"bytes1": 0.127}""")

        return b1 == f[f.float1]



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

        return b1 == f[f.bytes1]

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
