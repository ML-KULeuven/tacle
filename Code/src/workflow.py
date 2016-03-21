from constraint import SumColumn
from constraint_search import find_constraints
from idp import IDP
from minizinc import Minizinc
from parser import *
from group_assign import *
from constraint_search import find_constraints
from constraint import SumColumn
import argparse


def main(csv_file, groups_file):
	groups = get_groups_tables(csv_file, groups_file)
	constraint = SumColumn()
	assignments = find_groups(constraint, Minizinc(), groups)
	constraints = find_constraints(Minizinc(), constraint, assignments)
	print(constraints)


def arg_parser():
	p = argparse.ArgumentParser()
	p.add_argument('csv_file')
	p.add_argument('groups_file')
	return p


if __name__ == '__main__':
	main(**vars(arg_parser().parse_args()))
