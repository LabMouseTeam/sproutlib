from labmouse.sproutlib.Sproutlib import SproutRoot, SproutSchema
from threading import Thread
import json
import time
import sys


class Test(SproutRoot, Thread):
    class id(SproutSchema):
        type = int
        required = True

    class name(SproutSchema):
        required = True

    class email(SproutSchema):
        pass

    class thread(SproutSchema):
        hidden = True

    def __unpickle_all(self):
        if self.thread not in self:
            raise Exception('no thread defined')

    def __init__(self, *args, **kwargs):
        Thread.__init__(self)
        SproutRoot.__init__(self, *args, **kwargs)

        self.__unpickle_all()

        self.interrupted = False

    def join(self):
        self.interrupted = True
        Thread.join(self)

    def run(self):
        T = self[self.thread]

        print(' - performing max {} iterations'.format(T['iter']))

        i = 0
        while i < T['iter']:
            time.sleep(1)
            i += 1
            if self.interrupted is True:
                print('interrupted!')
                break

        print(' - performed {} iterations'.format(i))


if __name__ == "__main__":
    f = open(sys.argv[1], 'r')
    y = f.read()

    t = Test(y)
    t.start()

    print(' + thread running; waiting for 3 seconds...')
    time.sleep(3)
    t.join()

    print(t)
