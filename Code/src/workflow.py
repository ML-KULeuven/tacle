import argparse
import time

from core.constraint import *
from core.solutions import Solutions
from core.strategy import StrategyManager
from engine.idp import IdpAssignmentStrategy
from engine.internal import InternalCSPStrategy, InternalSolvingStrategy
from engine.minizinc import MinizincAssignmentStrategy, MinizincSolvingStrategy
from parse.parser import get_groups_tables

constraint_list = [
    # EqualGroup(),
    Permutation(),
    Series(),
    AllDifferent(),
    Projection(),
    Rank(),
    ForeignKey(),
    Lookup(),
    FuzzyLookup()
]

constraint_list += Aggregate.instances()
constraint_list += ConditionalAggregate.instances()

constraint_list += [
    RunningTotal(),
    ForeignProduct(),
    Product(),
    SumProduct(),
    Equal(),
]


def order_constraints(constraints: List[Constraint]):
    ordered = []
    found = set()
    spill = constraints
    while len(spill) > 0:
        new_spill = []
        for constraint in constraints:
            if constraint.depends_on().issubset(found):
                ordered.append(constraint)
                found.add(constraint)
            else:
                spill.append(constraint)
        if len(new_spill) == len(spill):
            raise Exception("Dependency order is not a DAG")
        spill = new_spill
    return ordered


def main(csv_file, groups_file, verbose, silent=False, parse_silent=False, constraints=constraint_list):
    manager = get_manager()
    groups = list(get_groups_tables(csv_file, groups_file, silent=parse_silent))

    solutions = Solutions()
    t_origin = time.time()

    supported = []
    unsupported_assignment = []
    unsupported_solving = []
    for constraint in constraints:
        if not manager.supports_assignments_for(constraint):
            unsupported_assignment.append(constraint)
        elif not manager.supports_solving_for(constraint):
            unsupported_solving.append(constraint)
        else:
            supported.append(constraint)

    if len(unsupported_assignment) > 0 and not silent:
        print("No assignment strategy for: {}".format(", ".join(str(c) for c in unsupported_assignment)))
    if len(unsupported_solving) > 0 and not silent:
        print("No solving strategies for: {}".format(", ".join(str(c) for c in unsupported_solving)))#
    if (len(unsupported_assignment) > 0 or len(unsupported_solving) > 0) and not silent:
        print()

    ordered = order_constraints(supported)

    for constraint in ordered:
        t_start = time.time()
        assignments = manager.find_assignments(constraint, groups, solutions)
        t_assign = time.time()
        solutions.add(constraint, manager.find_solutions(constraint, assignments, solutions))
        t_end = time.time()
        f_string = "{name} [assignment time: {assign:.3f}, solving time: {solve:.3f}]"
        if verbose and not silent:
            print(f_string.format(name=constraint.name, assign=t_assign - t_start, solve=t_end - t_assign))
        if len(solutions.get_solutions(constraint)) > 0 and not silent:
            print("\n".join(["\t" + constraint.to_string(s) for s in solutions.get_solutions(constraint)]))
        if (len(solutions.get_solutions(constraint)) > 0 or verbose) and not silent:
            print()

    if verbose and not silent:
        print("Total: {0:.3f}".format(time.time() - t_origin))

    return solutions


def get_manager():
    manager = StrategyManager()
    manager.add_assignment_strategy(InternalCSPStrategy())
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
    p.add_argument('-v', '--verbose', action="store_true")
    return p


if __name__ == '__main__':
    main(**vars(arg_parser().parse_args()))
