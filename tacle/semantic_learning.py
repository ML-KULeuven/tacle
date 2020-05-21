import time
import logging
import spacy
import re
import random
from spacy.tokens import Doc
from typing import List
from table_logger import TableLogger

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

#tbl = TableLogger(columns='column,template(random),total time, choice operation,assign,wi_assign,solve',float_format='{:,.4f}'.format)
tbl = TableLogger(columns='column,template,target,solution,assign,wi_assign,solve', float_format='{:,.4f}'.format)
nlp_dictionary = dict()

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


class MyDictionary(dict):
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


def get_template_nlp(templates):
    for template in templates:
        nlp_dictionary[template] = nlp("".join(clean(template.name)))


def rank_templates(header, templates):
    # TODO handle multiple row header
    #template_name = list(clean(template.name) for template in templates)
    # print("The word is: {} \n The list is this: {}".format(header, template_name))
    dictionary = dict()
    ordered = []

    if header:
        word_token = nlp(header)
    else:
        return templates

    if word_token and word_token.vector_norm:
        for template in templates:
            template_tokens = nlp_dictionary[template]
            # if not a noun phrase
            if not template_tokens.noun_chunks or sum(1 for e in template_tokens.noun_chunks) == 0:
                dictionary[template] = template_tokens.similarity(word_token)
            else:
                dictionary[template] = 0
                count = 0
                for chunk in template_tokens.noun_chunks:
                    count += 1
                    #print(
                    #chunk.text,
                    #chunk.has_vector,
                    #chunk.similarity(nlp("total")),
                    #chunk.vector_norm,
                    #chunk.root.text,
                    #chunk.root.dep_,
                    #chunk.root.head.text)
                    dictionary[template] = (dictionary[template]+chunk.similarity(word_token))/count

        sorted_dictionary = ((k, dictionary[k]) for k in sorted(dictionary, key=dictionary.get, reverse=True))

        for k, v in sorted_dictionary:
            #print(k, v)
            ordered.append(k)
        templates = ordered
    else:
        print("Can't rank templates for {}".format(header))
    return templates


def hand_engineering(header, templates):
    if header == 'Total':
        return [template for template in templates if template.name == 'sum (row)']
    else:
        return [Equal()]


def make_column_block(table, column):
    block_range = Range(column, 0, 1, table.range.height)
    vertical = Orientation.vertical
    return Block(
        table, block_range, vertical, [table.get_vector_type(column, vertical)]
    )


def split_block(block, index):
    blocks = []
    if block.vector_count() == 1:
        blocks = [block]
    elif index == 0:
        blocks = [block.sub_block(index + 1, block.vector_count() - 1 - index)]
    elif index == block.vector_count() - 1:
        blocks = [block.sub_block(0, index)]
    else:
        blocks = [block.sub_block(0, index), block.sub_block(index + 1, block.vector_count() - 1 - index)]
    return blocks


def learn(tables: List[Table], templates=None, solve_timeout=None):
    manager = get_manager(solve_timeout)

    solutions = (
        Solutions()
    )  # solutions = {}; properties = {}; canon_map = dict(); constraints = []  # type: List[Constraint]

    #t_origin = time.time()

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

    get_template_nlp(supported)

    t_origin = time.time()

    assign = 0
    solve = 0
    add = 0
    post = 0
    order_time = 0

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

        # For each column in the table
        for i in range(table.columns):
            c_start = time.time()
            c_assign = assign
            c_post = post
            c_solve = solve
            c_add = add

            target = make_column_block(table, i)
            # print("{}--> {}".format(headers[0][i],table.get_vector_data(i, Orientation.vertical)))
            header = "\n".join(
                [str(header_data[j, i]) for j in range(header_data.shape[0])]
            )

            o_start = time.time()
            ordered = rank_templates(header, supported)
            # randomly picked one constraint
            # ordered = [random.choice(supported)]
            # hand_engineered for magic_ice_cream.csv
            # ordered = hand_engineering(header, supported)
            o_stop = time.time()
            o_time = o_stop - o_start

            logger.debug("{}--> {}".format(header, list(order.name for order in ordered)))

            # Adapting blocks by removing current column
            new_blocks = []
            for block in blocks:
                new_blocks.append(block)
                if block.is_sub_block(target):
                    relative_index = target.vector_index() - block.vector_index()
                    splited_blocks = split_block(block, relative_index)
                    new_blocks.remove(block)
                    for b in splited_blocks:
                        new_blocks.append(b)

            # print(f"Block after: {new_blocks}")
            for template in ordered:
                logger.debug(
                    "Searching for template of type {}".format(template.name)
                )
                t_start = time.time()

                partial_assignment = {}
                if template.target:
                    # pre-check type consistency
                    domain = target if any(st in template.target.types for st in target.vector_types) else None
                    logger.debug(
                        "The target for template {}".format(domain)
                    )
                    if domain is None:
                        continue
                    partial_assignment = {template.target.name: target}

                #logger.debug("The target for template {}".format(domain))
                t_initial_assign = time.time()

                assignments = manager.find_assignments(
                    template, new_blocks, solutions, [partial_assignment]
                )
                t_assign = time.time()
                found = list(manager.find_solutions(template, assignments, solutions))
                logger.debug("found solution: {}".format(found))

                t_end = time.time()
                assign += t_assign - t_start
                post += t_assign - t_initial_assign
                solve += t_end - t_assign
                add += time.time() - t_end

                f_string = "Assignment time: {assign:.3f}, " \
                           "Without initial Assignment time: {after_initial:.3f}, " \
                           "solving time: {solve:.3f}] "
                logger.debug(
                    f_string.format(assign=t_assign - t_start, after_initial=t_assign - t_initial_assign,
                                    solve=t_end - t_assign)
                )

                tbl_assign = t_assign - t_start
                tbl_wi_assign = t_assign - t_initial_assign
                tbl_solve = t_end - t_assign
                tbl(header, template.name, domain, found, tbl_assign, tbl_wi_assign, tbl_solve)

                if len(found) > 0:
                    # TODO handle when two constraint exist in one row
                    # e.g. all-different, sum(row) for column 6
                    solutions.add(template, found)
                    break

            c_end = time.time()
            c_time = c_end - c_start
            logger.debug(
                "Column time: {0:.3f}"
                " (NLP time: {1:.3f}, "
                "Assign: {2:.3f}, "
                "Post Initial Assign {3:.3f}, "
                "Solve: {4:.3f}, "
                "Add: {5:.3f})".format(
                    c_time, o_time, assign - c_assign, post - c_post, solve - c_solve, add - c_add
                )
            )

            c_assign = assign - c_assign
            c_wi_assign = post - c_post
            c_solve = solve - c_solve

            order_time += o_time
            #print for random/hand engineered constaint
            #tbl(header, ordered[0].name, c_time, o_time, c_assign, c_wi_assign, c_solve)
            tbl(header, "", c_time, o_time, c_assign, c_wi_assign, c_solve)

    total_time = time.time() - t_origin
    logger.debug(
        "Total: {0:.3f} (Assign: {1:.3f}, Post Initial Assign {1:.3f}, Solve: {2:.3f}, Add: {3:.3f})".format(
            total_time, assign, post, solve, add
        )
    )

    logger.info("Total time {0:.3f}".format(total_time))
    print("Total time {0:.3f}, without ordering {1:.3f}".format(total_time, (total_time - order_time)))
    return solutions
