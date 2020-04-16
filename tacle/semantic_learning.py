import time
import logging
from typing import List

from .indexing import Table, Orientation, Range, Block
from .core.solutions import Solutions
from tacle.workflow import get_manager
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
)

logger = logging.getLogger(__name__)


def get_default_templates():
    constraint_list = [
        Equal(),
        # Permutation(),
        # Series(),
        # AllDifferent(),
        Projection(),
        # Rank(),
        # ForeignKey(),
        # Lookup(),
        # FuzzyLookup(),
        # RunningTotal(),
        # ForeignProduct(),
        # Product(),
        # Diff(),
        # PercentualDiff(),
        # SumProduct(),
        # Ordered(),
        # MutualExclusiveVector(),
    ]
    # constraint_list += MutualExclusivity.instances()
    constraint_list += Aggregate.instances()
    # constraint_list += ConditionalAggregate.instances()
    return constraint_list


def rank_templates(header, templates):
    # TODO Spacy code
    return templates


def make_column_block(table, column):
    block_range = Range(column, 0, 1, table.range.height)
    vertical = Orientation.vertical
    return Block(
        table, block_range, vertical, [table.get_vector_type(column, vertical)]
    )


def learn(tables: List[Table], templates=None, solve_timeout=None):
    manager = get_manager(solve_timeout)

    solutions = (
        Solutions()
    )  # solutions = {}; properties = {}; canon_map = dict(); constraints = []  # type: List[Constraint]

    t_origin = time.time()

    supported = []
    unsupported_assignment = []
    unsupported_solving = []

    for template in templates:
        if not manager.supports_assignments_for(template):
            unsupported_assignment.append(template)
        elif not manager.supports_solving_for(template):
            unsupported_solving.append(template)
        else:
            supported.append(template)

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

    assign = 0
    solve = 0
    add = 0
    blocks = [block for table in tables for block in table.blocks]

    for table in tables:
        if Orientation.vertical not in table.orientations:
            continue

        header_data = table.header_data[Orientation.horizontal]
        print(
            "Table - {}".format(table.name),
            header_data,
            table.header_ranges[Orientation.horizontal],
        )

        for i in range(table.columns):
            target = make_column_block(table, i)
            # print("{}--> {}".format(headers[0][i],table.get_vector_data(i, Orientation.vertical)))
            header = "\n".join(
                [str(header_data[j, i]) for j in range(header_data.shape[0])]
            )
            ordered = rank_templates(header, supported)

            print("{}--> {}".format(header, list(order.name for order in ordered)))

            for template in ordered:
                logger.debug(
                    "Searching for constraints of type {}".format(template.name)
                )
                t_start = time.time()

                partial_assignment = {}
                if template.target:
                    partial_assignment = {template.target.name: target}
                print(partial_assignment)

                # TODO Adapt the blocks (removing the column)
                assignments = manager.find_assignments(
                    template, blocks, solutions, [partial_assignment]
                )
                t_assign = time.time()
                found = list(manager.find_solutions(template, assignments, solutions))
                print("found solution: {}\n".format(found))

                if len(found) > 0:
                    solutions.add(template, found)
                    break

            t_before_add = time.time()
            # solutions.add(constraint, found)
            # print( "Here is my solution object after assignment:solutions {}\n, properties {}\n, constraints {}\n".format(
            # solutions.solutions, solutions.properties, solutions.constraints))
            t_end = time.time()
            assign += t_assign - t_start
            solve += t_before_add - t_assign
            add += t_end - t_before_add
            f_string = "Assignment time: {assign:.3f}, solving time: {solve:.3f}]"
            logger.debug(
                f_string.format(assign=t_assign - t_start, solve=t_end - t_assign)
            )

    total_time = time.time() - t_origin
    logger.debug(
        "Total: {0:.3f} (Assign: {1:.3f}, Solve: {2:.3f}, Add: {3:.3f})".format(
            total_time, assign, solve, add
        )
    )

    logger.info("Total time {0:.3f}".format(total_time))

    return solutions


def main(tables, templates=None, solve_timeout=None):
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
