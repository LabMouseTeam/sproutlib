from labmouse.sproutlib.Sproutlib import SproutRoot, SproutSchema
import sys


class Test(SproutRoot):
    class id(SproutSchema):
        type = int
        required = True

    class name(SproutSchema):
        required = True

    class email(SproutSchema):
        pass


if __name__ == "__main__":
    f = open(sys.argv[1], 'r')
    y = f.read()

    t = Test(y)
    print(t)

