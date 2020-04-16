import argparse
import time
import logging
import spacy
from spacy.tokens import Doc
import re

from .core.template import *
from .core.learning import LearningTask
from .core.solutions import Solutions
from .core.strategy import StrategyManager
from .engine.idp import IdpAssignmentStrategy
from .engine.internal import InternalCSPStrategy, InternalSolvingStrategy
from .engine.minizinc import MinizincAssignmentStrategy, MinizincSolvingStrategy
from .parse.parser import get_groups_tables, create_index_group
from .indexing import Table, Orientation, Range, Block

logger = logging.getLogger(__name__)

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


"""def get_constraint_list():
    constraint_list = [
        Equal(),
        AllDifferent(),
        Rank(),
        #RunningTotal(),
        Product(),
        Diff(),
        SumProduct(),
        Ordered(),
    ]
    constraint_list += Aggregate.instances()
    #constraint_list += ConditionalAggregate.instances()
    return constraint_list
"""
def get_constraint_list():
    constraint_list = [
        Equal(),
        Projection()
    ]
    constraint_list += Aggregate.instances()
    #constraint_list += ConditionalAggregate.instances()
    return constraint_list

def clean(str):
    str = re.sub('[- ]', '_', str)
    str = re.sub('[\W]+', '', str)
    str = re.sub('[_]+', ' ', str)
    return str

def order_constraints(word, constraints: List[ConstraintTemplate]):
    constraint_word= list(clean(constraint.name) for constraint in constraints)
    dictionary = dict()
    ordered = []

    #print("The word is: {} \n The list is this: {}".format(word, constraint_word))
    word_token = nlp(word)

    if (word_token and word_token.vector_norm):
        for constraint in constraints:
            constraint_tokens = nlp("".join(clean(constraint.name)))
            dictionary[constraint] = constraint_tokens.similarity(word_token)

            for chunk in constraint_tokens.noun_chunks:
                #print(chunk.text, chunk.has_vector, chunk.similarity(nlp("total")), chunk.vector_norm, chunk.root.text, chunk.root.dep_, chunk.root.head.text)
                dictionary[constraint] = chunk.similarity(word_token)

        sorted_dictionary = ((k, dictionary[k]) for k in sorted(dictionary, key=dictionary.get, reverse=True))

        for k, v in sorted_dictionary:
            #print(k, v)
            ordered.append(k)

        #print(ordered)
        return ordered
    else:
        return constraints


def task(csv_file, groups_file, constraints=None, manager=None):
    if constraints is None:
        constraints = get_constraint_list()
    if manager is None:
        manager = get_manager()
    return LearningTask(csv_file, groups_file, manager, constraints)


def make_column_block(table, column):
    block_range = Range(column, 0, 1, table.range.height)
    vertical = Orientation.vertical
    return Block(table, block_range, vertical, [table.get_vector_type(column, vertical)])


def main(data, csv_file, groups_file, tables: List[Table], verbose, silent=False, constraints=None, only_total_time=False, groups=None,
         solve_timeout=None):
    if only_total_time:
        silent = True
    manager = get_manager(solve_timeout)
    if groups is None:
        groups = list(get_groups_tables(csv_file, groups_file))

    print("The group is: {}".format(groups ))

    solutions = Solutions()  # solutions = {}; properties = {}; canon_map = dict(); constraints = []  # type: List[Constraint]

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

    assign = 0
    solve = 0
    add = 0

    for table in tables:
        print("Table- {}".format(table.name))
        headers=table.header.get_data(data)# Table.header--> Range

        for i in range(table.columns):
            target = make_column_block(table, i)
            #print("{}--> {}".format(headers[0][i],table.get_vector_data(i, Orientation.vertical)))
            ordered= supported
            #ordered= (order_constraints(headers[0][i], supported))
            print("{}--> {}".format(headers[0][i], list(order.name for order in ordered)))

            for constraint in ordered:
                logger.debug("Searching for constraints of type {}".format(constraint.name))
                t_start = time.time()

                target_group={}
                for variable in constraint.variables:
                    if variable.prime :
                        target_group= {variable.name: target}
                print(target_group)

                assignments = manager.find_assignments(constraint, groups, target_group, solutions)
                t_assign = time.time()
                found = list(manager.find_solutions(constraint, assignments, solutions))
                print("found solution: {}\n".format(found))

                if target_group in found:
                    solutions.add(constraint, found)
                    break

            t_before_add = time.time()
            #solutions.add(constraint, found)
            #print( "Here is my solution object after assignment:solutions {}\n, properties {}\n, constraints {}\n".format(
                        #solutions.solutions, solutions.properties, solutions.constraints))
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
    # StrategyManager-->self.assignment_strategies=[]
    #                  self.sloving_strategies= []
    manager.add_assignment_strategy(
        InternalCSPStrategy())  # assignment_strategies.append(AssignmentStrategy--> _contraints= set()); Add each constraint template in the object
    manager.add_solving_strategy(
        InternalSolvingStrategy())  # sloving_strategies.append(DictSovingStrategy--> strategies={}); Add constraint templemte as key and constraint func as value
    manager.add_assignment_strategy(
        IdpAssignmentStrategy())  # assignment_strategies.append(DictAssignmentStrategy-->strategies={});
    manager.add_assignment_strategy(
        MinizincAssignmentStrategy())  # assignment_strategies.append(DictAssignmentStrategy-->strategies={});
    # manager.add_solving_strategy(AspSolvingStrategy())
    manager.add_solving_strategy(
        MinizincSolvingStrategy())  # sloving_strategies.append(DictSovingStrategy--> strategies={});Probably add aggregate function to the dictionary
    return manager
