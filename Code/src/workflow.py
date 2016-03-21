import argparse

from constraint_search import find_constraints
from group_assign import *
from minizinc import Minizinc
from parser import *


def main(csv_file, groups_file):
	groups = get_groups_tables(csv_file, groups_file)
	constraint = SumColumn()
	assignments = find_groups(constraint, Minizinc(), groups)
	constraints = find_constraints(Minizinc(), constraint, assignments)
	print("Constraints:\n" + "\n".join([constraint.to_string(solution) for solution in constraints]))


def arg_parser():
	p = argparse.ArgumentParser()
	p.add_argument('csv_file')
	p.add_argument('groups_file')
	return p


if __name__ == '__main__':
	main(**vars(arg_parser().parse_args()))
