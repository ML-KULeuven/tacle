import itertools

import numpy

from core.constraint import *
from core.group import Group
from core.strategy import AssignmentStrategy, DictSolvingStrategy


class InternalAssignmentStrategy(AssignmentStrategy):
    def __init__(self):
        super().__init__()
        self.constraints = {Series(), AllDifferent(), Permutation(), Rank(), ForeignKey(), Lookup()}

    def applies_to(self, constraint):
        return constraint in self.constraints

    def apply(self, constraint: Constraint, groups: [Group], solutions):
        return constraint.source.candidates(groups, solutions, constraint.filters)


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

        def lookups(c: Lookup, assignments, solutions):
            results = []

            def is_lookup(reference_dictionary, keys, values):
                if len(keys) != len(values):
                    print("Unexpected case (differing lengths)")
                    return False
                for i in range(len(keys)):
                    if not keys[i] in reference_dictionary:
                        print("Unexpected case (key not present)")
                        return False
                    elif reference_dictionary[keys[i]] != values[i]:
                        return False
                return True

            for assignment in assignments:
                pk, pv, fk, fv = [assignment[k.name] for k in [c.o_key, c.o_value, c.f_key, c.f_value]]
                for pk_v, pv_v in itertools.product(pk, pv):
                    if not pk_v.overlaps_with(pv_v):
                        pk_dict = dict(zip(pk_v.get_vector(1), pv_v.get_vector(1)))
                        for fk_v, fv_v in itertools.product(fk, fv):
                            if not any(g1.overlaps_with(g2) for g1 in [pk_v, pv_v] for g2 in [fk_v, fv_v])\
                                    and not fk_v.overlaps_with(fv_v)\
                                    and is_lookup(pk_dict, fk_v.get_vector(1), fv_v.get_vector(1)):
                                result = {c.o_key: pk_v, c.o_value: pv_v, c.f_key: fk_v, c.f_value: fv_v}
                                results.append({k.name: v for k, v in result.items()})
            return results

        self.add_strategy(Series(), series)
        self.add_strategy(AllDifferent(), all_different)
        self.add_strategy(Permutation(), permutation)
        self.add_strategy(Rank(), rank)
        self.add_strategy(ForeignKey(), foreign_keys)
        self.add_strategy(Lookup(), lookups)

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
