import argparse

import time

from constraint_search import find_constraints
from group_assign import *
from internal import Internal
from minizinc import Minizinc
from parser import *


def main(csv_file, groups_file):
	engines = [Internal(), Minizinc()]
	t = time.time()
	groups = get_groups_tables(csv_file, groups_file)
	tg = time.time()
	constraints = [Permutation(), Series(), AllDifferent(), SumColumn(), SumRow()]
	assignments = {c: find_groups(c, assignment_engine(engines, c), groups) for c in constraints}
	ta = time.time()
	solutions = {c: find_constraints(solution_engine(engines, c), c, a) for c, a in assignments.items()}
	ts = time.time()

	print("Solutions:")
	for constraint in constraints:
		print(constraint.name)
		print("\n".join([constraint.to_string(s) for s in solutions[constraint]]))
		print()

	format_string = "Total: {0:.2f}, Group parsing: {1:.3f}, Assignments: {2:.3f}, Solutions: {3:.3f}"
	print(format_string.format(ts - t, tg - t, ta - tg, ts - ta))


def assignment_engine(engines, constraint):
	if len(engines) == 0:
		raise Exception("Could not find an engine for " + str(constraint))
	engine = engines[0]
	while not engine.supports_group_generation(constraint):
		return assignment_engine(engines[1:], constraint)
	return engine


def solution_engine(engines, constraint):
	if len(engines) == 0:
		raise Exception("Could not find an engine for " + str(constraint))
	engine = engines[0]
	while not engine.supports_constraint_search(constraint):
		return assignment_engine(engines[1:], constraint)
	return engine


def arg_parser():
	p = argparse.ArgumentParser()
	p.add_argument('csv_file')
	p.add_argument('groups_file')
	return p


if __name__ == '__main__':
	main(**vars(arg_parser().parse_args()))
