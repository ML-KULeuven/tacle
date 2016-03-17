from constraint import SumColumn
from constraint_search import find_constraints
from idp import IDP
from parser import get_groups_tables
from group_assign import find_groups


def main(csv_file, groups_file):
	groups = get_groups_tables(csv_file, groups_file)
	constraint = SumColumn()
	assignments = find_groups(constraint, IDP(), groups)
	print([a.keys() for a in assignments])
	constraints = find_constraints(constraint, assignments)
	print(constraints)


def arg_parser():
	import argparse
	p = argparse.ArgumentParser()
	p.add_argument('csv_file')
	p.add_argument('groups_file')
	return p


if __name__ == '__main__':
	main(**vars(arg_parser().parse_args()))
