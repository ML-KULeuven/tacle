import time
import logging
import spacy
import re
from spacy.tokens import Doc
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

class my_dictionary(dict):
    # __init__ function
    def __init__(self):
        self = dict()
        # Function to add key:value
    def add(self, key, value):
        self[key] = value

class WhitespaceTokenizer(object):
    def __init__(self, vocab):
        self.vocab = vocab
    def __call__(self, text):
        words = text.split(' ')
        # All tokens 'own' a subsequent space character in this tokenizer
        spaces = [True] * len(words)
        return Doc(self.vocab, words=words, spaces=spaces)

nlp = spacy.load("en_core_web_lg")
nlp.tokenizer = WhitespaceTokenizer(nlp.vocab)

def clean(str):
    str = re.sub('[- ]', '_', str)
    str = re.sub('[\W]+', '', str)
    str = re.sub('[_]+', ' ', str)
    return str

def rank_templates(header, templates):
    # TODO handle multiple row header
    tempplate_name = list(clean(template.name) for template in templates)
    dictionary = dict()
    ordered = []

    print("The word is: {} \n The list is this: {}".format(header, tempplate_name))
    word_token = nlp(header)

    if (word_token and word_token.vector_norm):
        for template in templates:
            template_tokens = nlp("".join(clean(template.name)))
            dictionary[template] = template_tokens.similarity(word_token)

            for chunk in template_tokens.noun_chunks:
                # print(chunk.text, chunk.has_vector, chunk.similarity(nlp("total")), chunk.vector_norm, chunk.root.text, chunk.root.dep_, chunk.root.head.text)
                dictionary[template] = chunk.similarity(word_token)

        sorted_dictionary = ((k, dictionary[k]) for k in sorted(dictionary, key=dictionary.get, reverse=True))

        for k, v in sorted_dictionary:
            # print(k, v)
            ordered.append(k)

        # print(ordered)
        templates = ordered
    else:
        print("Can't rank templates for {}".format(header))
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
                    "Searching for template of type {}".format(template.name)
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
                    #TODO handle when two constraint exist in one row
                    # e.g. all-different, sum(row) for column 6
                    solutions.add(template, found)
                    break

            t_before_add = time.time()
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

    ordered = order_templates(supported)
    assign = 0
    solve = 0
    add = 0
    blocks = [block for table in tables for block in table.blocks]
    for template in ordered:
        logger.debug("Searching for template of type {}".format(template.name))
        t_start = time.time()
        assignments = manager.find_assignments(template, blocks, solutions)
        t_assign = time.time()
        found = list(manager.find_solutions(template, assignments, solutions))
        t_before_add = time.time()
        solutions.add(template, found)
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
