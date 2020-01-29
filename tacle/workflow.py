import logging
import time
from typing import List

from .core.virtual_template import VirtualLookup, VirtualConditionalAggregate
from .indexing import Table, Orientation, Block, Range
from .core.solutions import Solutions
from .core.strategy import StrategyManager
from .core.template import (
    Aggregate,
    ConditionalAggregate,
    Equal,
    Permutation,
    Series,
    AllDifferent,
    Projection,
    Rank,
    ForeignKey,
    Lookup,
    FuzzyLookup,
    RunningTotal,
    ForeignProduct,
    Product,
    Diff,
    PercentualDiff,
    SumProduct,
    Ordered,
    MutualExclusivity,
    MutualExclusiveVector,
    ConstraintTemplate,
)
from .engine.native import InternalCSPStrategy, InternalSolvingStrategy

logger = logging.getLogger(__name__)


def get_default_templates():
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
        MutualExclusiveVector(),
    ]
    constraint_list += MutualExclusivity.instances()
    constraint_list += Aggregate.instances()
    constraint_list += ConditionalAggregate.instances()
    return constraint_list


def get_default_virtual_templates():
    return [VirtualLookup()] + VirtualConditionalAggregate.instances()


def order_templates(constraints: List[ConstraintTemplate]):
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


# def task(csv_file, groups_file, constraints=None, manager=None):
#     if constraints is None:
#         constraints = get_default_templates()
#     if manager is None:
#         manager = get_manager()
#     return LearningTask(csv_file, groups_file, manager, constraints)
#
#
def make_virtual_block(table, orientation, block_type):
    # type: (Table, Orientation, str) -> Block
    if orientation == Orientation.vertical:
        b_range = Range(-1, 0, 1, table.range.height)
    else:
        b_range = Range(0, -1, table.range.width, 1)
    return Block(table, b_range, orientation, virtual=(block_type, False))


def main(tables, templates=None, solve_timeout=None):
    manager = get_manager(solve_timeout)

    solutions = Solutions()
    t_origin = time.time()

    supported = []
    unsupported_assignment = []
    unsupported_solving = []
    for constraint in templates:
        if not manager.supports_assignments_for(constraint):
            unsupported_assignment.append(constraint)
        elif not manager.supports_solving_for(constraint):
            unsupported_solving.append(constraint)
        else:
            supported.append(constraint)

    if len(unsupported_assignment) > 0:
        logger.info(
            "No assignment strategy for: {}".format(
                ", ".join(str(c) for c in unsupported_assignment)
            )
        )
    if len(unsupported_solving) > 0:
        logger.info(
            "No solving strategies for: {}".format(
                ", ".join(str(c) for c in unsupported_solving)
            )
        )

    ordered = order_templates(supported)
    assign = 0
    solve = 0
    add = 0
    blocks = [block for table in tables for block in table.blocks]
    for constraint in ordered:
        logger.debug("Searching for constraints of type {}".format(constraint.name))
        t_start = time.time()
        assignments = manager.find_assignments(constraint, blocks, solutions)
        t_assign = time.time()
        found = list(manager.find_solutions(constraint, assignments, solutions))
        t_before_add = time.time()
        solutions.add(constraint, found)
        t_end = time.time()
        assign += t_assign - t_start
        solve += t_before_add - t_assign
        add += t_end - t_before_add

        f_string = "Assignment time: {assign:.3f}, solving time: {solve:.3f}]"
        logger.debug(f_string.format(assign=t_assign - t_start, solve=t_end - t_assign))

    total_time = time.time() - t_origin
    logger.debug(
        "Total: {0:.3f} (Assign: {1:.3f}, Solve: {2:.3f}, Add: {3:.3f})".format(
            total_time, assign, solve, add
        )
    )

    logger.info("Total time {0:.3f}".format(total_time))
    return solutions


def get_manager(solve_timeout=None):
    manager = StrategyManager(timeout=solve_timeout)
    manager.add_assignment_strategy(InternalCSPStrategy())
    manager.add_solving_strategy(InternalSolvingStrategy())
    # manager.add_assignment_strategy(IdpAssignmentStrategy())
    # manager.add_assignment_strategy(MinizincAssignmentStrategy())
    # manager.add_solving_strategy(AspSolvingStrategy())
    # manager.add_solving_strategy(MinizincSolvingStrategy())
    return manager
