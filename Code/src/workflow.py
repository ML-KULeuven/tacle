import argparse
import time

from aspengine import AspSolvingStrategy
from core.constraint import *
from core.solutions import Solutions
from core.strategy import StrategyManager
from idp import IdpAssignmentStrategy
from internal import InternalAssignmentStrategy, InternalSolvingStrategy
from minizinc import MinizincAssignmentStrategy
from minizinc import MinizincSolvingStrategy
from parser import get_groups_tables


def main(csv_file, groups_file=None):
    manager = get_manager()
    groups = list(get_groups_tables(csv_file, groups_file))

    solutions = Solutions()
    t_origin = time.time()

    constraints = [Permutation(), Series(), AllDifferent(), SumColumn(), SumRow(), Rank(), ForeignKey(), Lookup(),
                   SumIf(), MaxIf(), RunningTotal(), ForeignProduct()]
    for constraint in constraints:
        if not manager.supports_assignments_for(constraint):
            print("No assignment strategy for {}\n".format(constraint))
        elif not manager.supports_solving_for(constraint):
            print("No solving strategy for {}\n".format(constraint))
        else:
            t_start = time.time()
            assignments = manager.find_assignments(constraint, groups, solutions)
            t_assign = time.time()
            solutions.add(constraint, manager.find_solutions(constraint, assignments, solutions))
            t_end = time.time()
            f_string = "{name} [assignment time: {assign:.3f}, solving time: {solve:.3f}]"
            print(f_string.format(name=constraint.name.capitalize(), assign=t_assign - t_start, solve=t_end - t_assign))
            print("\n".join(["\t" + constraint.to_string(s) for s in solutions.get_solutions(constraint)]))
            print()

    print("Total: {0:.3f}".format(time.time() - t_origin))


def get_manager():
    manager = StrategyManager()
    manager.add_assignment_strategy(InternalAssignmentStrategy())
    manager.add_solving_strategy(InternalSolvingStrategy())
    manager.add_assignment_strategy(IdpAssignmentStrategy())
    manager.add_assignment_strategy(MinizincAssignmentStrategy())
    # manager.add_solving_strategy(AspSolvingStrategy())
    manager.add_solving_strategy(MinizincSolvingStrategy())
    return manager


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('csv_file')
    p.add_argument('-g', '--groups_file', default=None)
    return p


if __name__ == '__main__':
    main(**vars(arg_parser().parse_args()))
