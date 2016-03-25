import os
from subprocess import Popen, PIPE, STDOUT

from constraint import *
from group import *


class Engine:
	def __init__(self):
		super().__init__()
		self.assignment_handler = ConstraintHandler.empty()
		self.solving_handler = ConstraintHandler.empty()

	def add_assignment_handler(self, handler: ConstraintHandler):
		self.assignment_handler.add(handler)

	def add_solving_handler(self, handler: ConstraintHandler):
		self.solving_handler.add(handler)

	def generate_groups(self, constraint: Constraint, groups: [Group], solutions) -> [[Group]]:
		raise NotImplementedError()

	def supports_group_generation(self, constraint: Constraint):
		raise NotImplementedError()

	def find_constraints(self, constraint: Constraint, assignments: [{Group}], solutions) -> [{(Group, int)}]:
		raise NotImplementedError()

	def supports_constraint_search(self, constraint: Constraint):
		raise NotImplementedError()


def run_command(command, input_data=None):
	if isinstance(input_data, str):
		input_data = input_data.encode("utf-8")
	p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
	data = p.communicate(input=input_data)

	# noinspection PyUnresolvedReferences
	return data[0].decode("utf-8")


def local(filename):
	return os.path.dirname(os.path.realpath(__file__)) + "/../" + filename
