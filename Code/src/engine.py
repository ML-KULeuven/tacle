from subprocess import Popen, PIPE, STDOUT

from constraint import *
from group import *


class Engine:
	def __init__(self):
		super().__init__()

	def generate_groups(self, constraint: Constraint, groups: [Group]) -> [[Group]]:
		raise NotImplementedError()


def run_command(command, input_data=None):
	if isinstance(input_data, str):
		input_data = input_data.encode("utf-8")
	p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
	data = p.communicate(input=input_data)

	# output = subprocess.check_output(command)

	# noinspection PyUnresolvedReferences
	return data[0].decode("utf-8")
