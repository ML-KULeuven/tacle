import argparse
import time
import logging

from .core.template import *
from .core.learning import LearningTask
from .core.solutions import Solutions
from .core.strategy import StrategyManager
from .engine.idp import IdpAssignmentStrategy
from .engine.internal import InternalCSPStrategy, InternalSolvingStrategy
from .engine.minizinc import MinizincAssignmentStrategy, MinizincSolvingStrategy
from .parse.parser import get_groups_tables

logger = logging.getLogger(__name__)


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
        MutualExclusivity(),
        MutualExclusiveVector()
    ]
    constraint_list += Aggregate.instances()
    constraint_list += ConditionalAggregate.instances()
    return constraint_list


def order_constraints(constraints: List[ConstraintTemplate]):
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


def task(csv_file, groups_file, constraints=None, manager=None):
    if constraints is None:
        constraints = get_constraint_list()
    if manager is None:
        manager = get_manager()
    return LearningTask(csv_file, groups_file, manager, constraints)


def main(csv_file, groups_file, verbose, silent=False, constraints=None, only_total_time=False, groups=None,
         solve_timeout=None):
    if only_total_time:
        silent = True
    manager = get_manager(solve_timeout)
    if groups is None:
        groups = list(get_groups_tables(csv_file, groups_file))

    print("The group is: {}".format(groups))

    solutions = Solutions()#solutions = {}; properties = {}; canon_map = dict(); constraints = []  # type: List[Constraint]

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
    

    if len(unsupported_assignment) > 0:
        logger.info("No assignment strategy for: {}".format(", ".join(str(c) for c in unsupported_assignment)))
    if len(unsupported_solving) > 0:
        logger.info("No solving strategies for: {}".format(", ".join(str(c) for c in unsupported_solving)))

    ordered = order_constraints(supported)

    assign = 0
    solve = 0
    add = 0

    #I should order the constraint based on constraint.name

    for constraint in ordered:
        logger.debug("Searching for constraints of type {}".format(constraint.name))
        t_start = time.time()

        assignments = manager.find_assignments(constraint, groups, solutions)

        print("Hello from workflow")
        t_assign = time.time()

        found = list(manager.find_solutions(constraint, assignments, solutions))

        print("found solution: {}\n".format(found))
        t_before_add = time.time()

        solutions.add(constraint, found)

        print("Here is my solution object after assignment:solutions {}\n, properties {}\n, constraints {}\n".format(
            solutions.solutions, solutions.properties, solutions.constraints))
        t_end = time.time()
        assign += t_assign - t_start
        solve += t_before_add - t_assign
        add += t_end - t_before_add

        f_string = "Assignment time: {assign:.3f}, solving time: {solve:.3f}]"
        logger.debug(f_string.format(assign=t_assign - t_start, solve=t_end - t_assign))

    total_time = time.time() - t_origin
    logger.debug("Total: {0:.3f} (Assign: {1:.3f}, Solve: {2:.3f}, Add: {3:.3f})"
                 .format(total_time, assign, solve, add))

    logger.info("Total time {0:.3f}".format(total_time))
    return solutions


def get_manager(solve_timeout=None):
    manager = StrategyManager(timeout=solve_timeout)
    #StrategyManager-->self.assignment_strategies=[]
    #                  self.sloving_strategies= []
    manager.add_assignment_strategy(InternalCSPStrategy())#assignment_strategies.append(AssignmentStrategy--> _contraints= set()); Add each constraint template in the object
    manager.add_solving_strategy(InternalSolvingStrategy())#sloving_strategies.append(DictSovingStrategy--> strategies={}); Add constraint templemte as key and constraint func as value
    manager.add_assignment_strategy(IdpAssignmentStrategy())#assignment_strategies.append(DictAssignmentStrategy-->strategies={});
    manager.add_assignment_strategy(MinizincAssignmentStrategy())#assignment_strategies.append(DictAssignmentStrategy-->strategies={});
    # manager.add_solving_strategy(AspSolvingStrategy())
    manager.add_solving_strategy(MinizincSolvingStrategy())#sloving_strategies.append(DictSovingStrategy--> strategies={});Probably add aggregate function to the dictionary
    return manager
