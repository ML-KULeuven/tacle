import argparse
import time

from core.constraint import *
from core.learning import LearningTask
from core.solutions import Solutions
from core.strategy import StrategyManager
from engine.idp import IdpAssignmentStrategy
from engine.internal import InternalCSPStrategy, InternalSolvingStrategy
from engine.minizinc import MinizincAssignmentStrategy, MinizincSolvingStrategy
from parse.parser import get_groups_tables


def get_constraint_list():
    constraint_list = [
        Equal(),
        # EqualGroup(),
        Permutation(),
        Series(),
        AllDifferent(),
        Projection(),
        Rank(),
        ForeignKey(),
        Lookup(),
        FuzzyLookup(),
        RunningTotal(),
        ForeignProduct(),
        Product(),
        Diff(),
        PercentualDiff(),
        SumProduct(),
        Ordered(),
    ]
    constraint_list += Aggregate.instances()
    constraint_list += ConditionalAggregate.instances()
    return constraint_list


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


def task(csv_file, groups_file, constraints=None):
    if constraints is None:
        constraints = get_constraint_list()
    return LearningTask(csv_file, groups_file, get_manager(), constraints)


def main(csv_file, groups_file, verbose, silent=False, constraints=None, only_total_time=False):
    if only_total_time:
        silent = True
    manager = get_manager()
    groups = list(get_groups_tables(csv_file, groups_file))

    solutions = Solutions()
    t_origin = time.time()

    supported = []
    unsupported_assignment = []
    unsupported_solving = []
    if constraints is None:
        constraints = get_constraint_list()
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
    assign = 0
    solve = 0
    add = 0
    for constraint in ordered:
        if verbose and not silent:
            print(constraint.name, end=" ", flush=True)
        t_start = time.time()
        assignments = manager.find_assignments(constraint, groups, solutions)
        t_assign = time.time()
        found = list(manager.find_solutions(constraint, assignments, solutions))
        t_before_add = time.time()
        solutions.add(constraint, found)
        t_end = time.time()
        assign += t_assign - t_start
        solve += t_before_add - t_assign
        add += t_end - t_before_add
        if verbose and not silent:
            f_string = "[assignment time: {assign:.3f}, solving time: {solve:.3f}]"
            print(f_string.format(assign=t_assign - t_start, solve=t_end - t_assign))
        if len(solutions.get_solutions(constraint)) > 0 and not silent:
            print("\n".join(["\t" + constraint.to_string(s) for s in solutions.get_solutions(constraint)]))
        if (len(solutions.get_solutions(constraint)) > 0 or verbose) and not silent:
            print()

    total_time = time.time() - t_origin
    if verbose and not silent: #or True: # TODO:
        print("Total: {0:.3f} (Assign: {1:.3f}, Solve: {2:.3f}, Add: {3:.3f})".format(total_time, assign, solve, add))

    print("{0:.3f}".format(total_time))

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
    p.add_argument('-t', '--only_total_time', action="store_true")
    return p


if __name__ == '__main__':
    main(**vars(arg_parser().parse_args()))
