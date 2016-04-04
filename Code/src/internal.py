import itertools

import numpy

from core.constraint import *
from core.group import Group
from core.strategy import AssignmentStrategy, DictSolvingStrategy


class InternalAssignmentStrategy(AssignmentStrategy):
    def __init__(self):
        super().__init__()
        self.constraints = {Series(), AllDifferent(), Permutation(), Rank(), ForeignKey(), Lookup(), FuzzyLookup(),
                            SumIf(), MaxIf(), RunningTotal(), ForeignProduct()}

    def applies_to(self, constraint):
        return constraint in self.constraints

    def apply(self, constraint: Constraint, groups: [Group], solutions):
        return constraint.source.candidates(groups, solutions, constraint.filters)


class InternalSolvingStrategy(DictSolvingStrategy):
    def __init__(self):
        super().__init__()

        def series(c: Series, assignments, solutions):
            def test_list(vector):
                for i in range(len(vector)):
                    if not vector[i] == i + 1:
                        return False
                return True

            return self._generate_test_vectors(assignments, [c.x], test_list)

        def all_different(c: AllDifferent, assignments, solutions):
            return self._generate_test_vectors(assignments, [c.x], lambda v: len(set(v)) == len(v))

        def permutation(c: Permutation, assignments, solutions):
            def test_set(vector):
                number_set = set(range(1, len(vector) + 1))
                for i in range(len(vector)):
                    if not vector[i] in number_set:
                        return False
                    number_set.remove(vector[i])
                return True

            return self._generate_test_vectors(assignments, [c.x], test_set)

        def rank(c: Rank, assignments, solutions):
            def is_rank(y, x):
                return (numpy.array(rank_data(x)) == y).all()

            return self._generate_test_vectors(assignments, [c.y, c.x], is_rank)

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
                            if not any(g1.overlaps_with(g2) for g1 in [pk_v, pv_v] for g2 in [fk_v, fv_v]) \
                                    and not fk_v.overlaps_with(fv_v) \
                                    and is_lookup(pk_dict, fk_v.get_vector(1), fv_v.get_vector(1)):
                                result = {c.o_key: pk_v, c.o_value: pv_v, c.f_key: fk_v, c.f_value: fv_v}
                                results.append({k.name: v for k, v in result.items()})
            return results

        def fuzzy_lookup(c: Lookup, assignments, solutions):
            keys = [c.o_key, c.o_value, c.f_key, c.f_value]

            def find_fuzzy(element, collection):
                if element < collection[0]:
                    return None
                for i in range(1, len(collection)):
                    if element < collection[i]:
                        return i - 1
                return len(collection) - 1

            def is_lookup(ok, ov, fk, fv):
                exact = True
                for i in range(len(fk)):
                    index = find_fuzzy(fk[i], ok)
                    if index is not None and ok[index] != fk[i]:
                        exact = False
                    if index is None or not equal(ov[index], fv[i]):
                        return False
                return not exact

            return self._generate_test_vectors(assignments, keys, is_lookup)

        def conditional_aggregate(c: ConditionalAggregate, assignments, solutions):
            keys = [c.o_key, c.result, c.f_key, c.values]

            def is_aggregate(ok_v, r_v, fk_v, v_v):
                m = dict(zip(ok_v, range(len(ok_v))))
                acc = [None] * len(r_v)
                for i in range(len(fk_v)):
                    key = m[fk_v[i]]
                    acc[key] = v_v[i] if acc[key] is None else c.operator(acc[key], v_v[i])
                acc = [c.default if acc[i] is None else acc[i] for i in range(len(acc))]
                return all(equal(r_v[i], acc[i]) for i in range(len(r_v)))

            return list(self._generate_test_vectors(assignments, keys, is_aggregate))

        def running_total(c: RunningTotal, assignments, solutions):
            def is_running_diff(acc, pos, neg):
                if not acc[0] == pos[0] - neg[0]:
                    return False
                for i in range(1, len(acc)):
                    if not equal(acc[i], acc[i - 1] + pos[i] - neg[i]):
                        return False
                return True

            return self._generate_test_vectors(assignments, [c.acc, c.pos, c.neg], is_running_diff)

        def foreign_operation(c: ForeignOperation, assignments, solutions):
            keys = [c.o_key, c.f_key, c.result, c.o_value, c.f_value]

            def is_foreign_product(ok, fk, r, ov, fv):
                m = dict(zip(ok, ov))
                for i in range(len(fk)):
                    if not equal(r[i], c.operator(fv[i], m[fk[i]])):
                        return False
                return True

            return self._generate_test_vectors(assignments, keys, is_foreign_product)

        self.add_strategy(Series(), series)
        self.add_strategy(AllDifferent(), all_different)
        self.add_strategy(Permutation(), permutation)
        self.add_strategy(Rank(), rank)
        self.add_strategy(ForeignKey(), foreign_keys)
        self.add_strategy(Lookup(), lookups)
        self.add_strategy(FuzzyLookup(), fuzzy_lookup)
        self.add_strategy(SumIf(), conditional_aggregate)
        self.add_strategy(MaxIf(), conditional_aggregate)
        self.add_strategy(RunningTotal(), running_total)
        self.add_strategy(ForeignProduct(), foreign_operation)

    @staticmethod
    def _generate_test_vectors(assignments, keys, test_f):
        results = []
        for assignment in assignments:
            for vectors in itertools.product(*[assignment[k.name] for k in keys]):
                if not any(g1.overlaps_with(g2) for g1, g2 in itertools.combinations(vectors, 2)) \
                        and test_f(*list(map(lambda vec: vec.get_vector(1), vectors))):
                    results.append(dict(zip([k.name for k in keys], vectors)))
        return results


def rank_data(a):
    initial = sorted(a, reverse=True)
    table = {initial[0]: 1}
    counter = 1
    for i in range(1, len(initial)):
        if initial[i] == initial[i - 1]:
            counter += 1
        else:
            table[initial[i]] = table[initial[i - 1]] + counter
            counter = 1
    return [table[e] for e in a]


def equal(x, y):
    delta = pow(10, -10)
    if isinstance(x, float) or isinstance(y, float):
        return abs(x - y) < delta
    else:
        return x == y
