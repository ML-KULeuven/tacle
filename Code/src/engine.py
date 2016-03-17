import subprocess

from constraint import *
from group import *


class Engine:
	def __init__(self):
		super().__init__()

	def generate_groups(self, constraint: Constraint, groups: [Group]) -> [[Group]]:
		raise NotImplementedError()


def run_command(command):
	p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	return iter(p.stdout.readline, b'')
