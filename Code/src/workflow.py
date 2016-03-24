import argparse

import time

from constraint_search import find_constraints
from group_assign import *
from minizinc import Minizinc
from parser import *
from aspengine import ASP
from group_assign import *
from constraint import SumColumn
import argparse

def main(csv_file, groups_file):
  t = time.time()
  groups = get_groups_tables(csv_file, groups_file)
  print("groups time", time.time()-t)
  constraints = [SumColumn(), SumRow()]
  t_zinc = time.time()
  assignments = [find_groups(constraint, Minizinc(), groups) for constraint in constraints]
  solutions = [find_constraints(Minizinc(), c, a) for c, a in zip(constraints, assignments)]
  print("zinc time:", time.time() - t_zinc)
  t_asp = time.time()
  solutions = [find_constraints(ASP(), c, a) for c, a in zip(constraints, assignments)]
  print("asp time:", time.time() - t_asp)
# print("Constraints:")
# print("\n".join(["\n".join([c.to_string(s) for s in l]) for c, l in zip(constraints, solutions)]))


def arg_parser():
  p = argparse.ArgumentParser()
  p.add_argument('csv_file')
  p.add_argument('groups_file')
  return p


if __name__ == '__main__':
  main(**vars(arg_parser().parse_args()))
