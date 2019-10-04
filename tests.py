from labmouse.sproutlib.Sproutlib import SproutRoot, SproutSchema
import unittest
import sys


class TestBytes(unittest.TestCase):
    def test_basic(self):
        class Foo(SproutRoot):
            class bytes1(SproutSchema):
                required = True
                type = bytes

        f = Foo({'bytes1': b'\x11\x22\x33\x44'})
        b = f['bytes1']

        print(b)
        print(f)


if __name__ == "__main__":
    unittest.main()
