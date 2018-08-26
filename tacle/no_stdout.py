# http://stackoverflow.com/a/2829036/253387
import contextlib
import sys


class DummyFile(object):
    def write(self, x):
        pass


@contextlib.contextmanager
def no_stdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = save_stdout
