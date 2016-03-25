import argparse

import time

from constraint_search import find_constraints
from group_assign import *
from internal import Internal
from minizinc import Minizinc
from parser import *
from group_assign import *
from constraint import SumColumn
from solutions import Solutions


def main(csv_file, groups_file):
	engines = [Internal(), Minizinc()]
	groups = get_groups_tables(csv_file, groups_file)

	solutions = Solutions()
	t_origin = time.time()
	constraints = [Permutation(), Series(), AllDifferent(), SumColumn(), SumRow(), Rank(), ForeignKey()]
	for constraint in constraints:
		t_start = time.time()
		assignments = find_groups(constraint, assignment_engine(engines, constraint), groups, solutions)
		t_assign = time.time()
		engine = solution_engine(engines, constraint)
		solutions.add(constraint, find_constraints(engine, constraint, assignments, solutions))
		t_end = time.time()
		f_string = "{name} [assignment time: {assign:.3f}, solving time: {solve:.3f}]"
		print(f_string.format(name=constraint.name.capitalize(), assign=t_assign - t_start, solve=t_end - t_assign))
		print("\n".join(["\t" + constraint.to_string(s) for s in solutions.get_solutions(constraint)]))
		print()

	print("Total: {0:.3f}".format(time.time() - t_origin))


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
