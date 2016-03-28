import numpy

from constraint import *
from group import Group
from strategy import DictAssignmentStrategy, DictSolvingStrategy


class InternalAssignmentStrategy(DictAssignmentStrategy):
    def __init__(self):
        super().__init__()

        def series(constraint, groups, solutions):
            return [{constraint.get_variables()[0].name: g} for g in filter(Group.is_integer, groups)]

        def all_different(constraint, groups, solutions):
            return [{constraint.get_variables()[0].name: g} for g in filter(Group.is_textual, groups)]

        def permutation(constraint, groups, solutions):
            return [{constraint.get_variables()[0].name: g} for g in filter(Group.is_integer, groups)]

        def rank(constraint, groups, solutions):
            assignments = []
            for y_group in solutions.get_property_groups(Permutation()):
                for x_group in filter(Group.is_numeric, groups):
                    if x_group.length() == y_group.length():
                        assignments.append({"Y": y_group, "X": x_group})
            return assignments

        def foreign_keys(constraint, groups, solutions):
            assignments = []
            for pk_group in solutions.get_property_groups(AllDifferent()):
                for fk_group in filter(Group.is_textual, groups):
                    if not pk_group.is_subgroup(fk_group):
                        assignments.append({constraint.pk.name: pk_group, constraint.fk.name: fk_group})
            return assignments

        self.add_strategy(Series(), series)
        self.add_strategy(AllDifferent(), all_different)
        self.add_strategy(Permutation(), permutation)
        self.add_strategy(Rank(), rank)
        self.add_strategy(ForeignKey(), foreign_keys)


class InternalSolvingStrategy(DictSolvingStrategy):
    def __init__(self):
        super().__init__()

        def series(constraint, assignments, solutions):
            results = []
            variable = constraint.get_variables()[0]
            for group in [assignment[variable.name] for assignment in assignments]:
                for i in range(1, group.vectors() + 1):
                    if self.test_list(group.get_vector(i)):
                        results.append({variable.name: group.vector_subset(i, i)})
            return results

        def all_different(constraint, assignments, solutions):
            results = []
            variable = constraint.get_variables()[0]
            for group in [assignment[variable.name] for assignment in assignments]:
                for i in range(1, group.vectors() + 1):
                    vector = group.get_vector(i)
                    if len(set(vector)) == len(vector):
                        results.append({variable.name: group.vector_subset(i, i)})
            return results

        def permutation(constraint, assignments, solutions):
            results = []
            variable = constraint.get_variables()[0]
            for group in [assignment[variable.name] for assignment in assignments]:
                for i in range(1, group.vectors() + 1):
                    if self.test_set(group.get_vector(i)):
                        results.append({variable.name: group.vector_subset(i, i)})
            return results

        def rank(constraint, assignments, solutions):
            solutions = []
            for assignment in assignments:
                y_group = assignment["Y"]
                x_group = assignment["X"]
                for i in range(1, y_group.vectors() + 1):  # TODO invert
                    for j in range(1, x_group.vectors() + 1):
                        x_v = x_group.vector_subset(j, j)
                        y_v = y_group.vector_subset(i, i)
                        if not x_v.overlaps_with(y_v):
                            indices = numpy.argsort(x_group.get_vector(j)) + 1
                            if all(indices[::-1] == y_group.get_vector(i)):
                                solutions.append({"X": x_v, "Y": y_v})
            return solutions

        def foreign_keys(constraint, assignments, solutions):
            solutions = []
            for assignment in assignments:
                pk_group = assignment[constraint.pk.name]
                fk_group = assignment[constraint.fk.name]

                fk_vectors = [fk_group.vector_subset(j, j) for j in range(1, fk_group.vectors() + 1)]
                fk_sets = map(lambda v: (v, set(v.get_vector(1))), fk_vectors)

                pk_vectors = [pk_group.vector_subset(j, j) for j in range(1, pk_group.vectors() + 1)]
                pk_sets = map(lambda v: (v, set(v.get_vector(1))), pk_vectors)

                for (pk, pk_set) in pk_sets:
                    for (fk, fk_set) in fk_sets:
                        if not pk.overlaps_with(fk) and pk_set >= fk_set:
                            solutions.append({constraint.pk.name: pk, constraint.fk.name: fk})
            return solutions

        self.add_strategy(Series(), series)
        self.add_strategy(AllDifferent(), all_different)
        self.add_strategy(Permutation(), permutation)
        self.add_strategy(Rank(), rank)
        self.add_strategy(ForeignKey(), foreign_keys)

    @staticmethod
    def test_set(vector):
        number_set = set(range(1, len(vector) + 1))
        for i in range(len(vector)):
            if not vector[i] in number_set:
                return False
            number_set.remove(vector[i])
        return True

    @staticmethod
    def test_list(vector):
        for i in range(len(vector)):
            if not vector[i] == i + 1:
                return False
        return True
