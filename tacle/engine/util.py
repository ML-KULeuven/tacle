import os
import tempfile
from subprocess import Popen, PIPE, STDOUT


def run_command(command, input_data=None):
    if isinstance(input_data, str):
        input_data = input_data.encode("utf-8")
    p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    data = p.communicate(input=input_data)

    # noinspection PyUnresolvedReferences
    return data[0].decode("utf-8")


def local(filename):
    return os.path.dirname(os.path.realpath(__file__)) + "/../../" + filename


class TempFile:
    def __init__(self, content, extension):
        self.file = tempfile.NamedTemporaryFile("w+", delete=False, suffix=("." + extension))
        print(content, file=self.file)
        self.file.close()
        self.name = self.file.name

    def delete(self):
        os.remove(self.file.name)
