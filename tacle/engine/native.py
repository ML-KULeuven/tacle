import functools
import itertools

import math
from collections import defaultdict

import numpy

from tacle.engine import evaluate
from tacle.core.virtual_template import VirtualLookup, VirtualConditionalAggregate
from tacle.core.template import *
from tacle.core.solutions import Solutions
from tacle.core.strategy import AssignmentStrategy, DictSolvingStrategy


class MaxRange:
    def __init__(self, test: callable):
        self._test = test

    def find(self, start, end, size, limit=None, last=None):
        limit = start + size - 1 if limit is None else limit
        last = end if last is None else last
        self._find(start, end, size, limit, last)

    def _find(self, start, end, size, limit, last):
        while True:
            if last - start < size:
                return
            elif (
                end - start < size or end < limit
            ):  # TODO Check change from end <= limit
                start += 1
                end = last
                limit = max(start + size, limit)
            else:
                if self._test(start, end):
                    start += 1
                else:
                    end -= 1


# TODO Sum IF with Nones
class InternalCSPStrategy(AssignmentStrategy):
    def __init__(self):
        super().__init__()
        self._constraints = set()

        self.add_constraint(Equal())
        self.add_constraint(EqualGroup())
        self.add_constraint(Series())
        self.add_constraint(AllDifferent())
        self.add_constraint(Permutation())
        self.add_constraint(Rank())
        self.add_constraint(ForeignKey())
        self.add_constraint(VirtualLookup())
        self.add_constraint(Lookup())
        self.add_constraint(FuzzyLookup())
        for c in VirtualConditionalAggregate.instances():
            self.add_constraint(c)
        for c in ConditionalAggregate.instances():
            self.add_constraint(c)
        for c in ConditionalAggregate2.instances():
            self.add_constraint(c)
        self.add_constraint(RunningTotal())
        self.add_constraint(ForeignProduct())
        self.add_constraint(Projection())
        for c in Aggregate.instances():
            self.add_constraint(c)
        self.add_constraint(Product())
        self.add_constraint(Diff())
        self.add_constraint(PercentualDiff())
        self.add_constraint(SumProduct())
        self.add_constraint(Ordered())
        for c in MutualExclusivity.instances():
            self.add_constraint(c)
        self.add_constraint(MutualExclusiveVector())
        for c in GroupedAggregate.instances():
            self.add_constraint(c)

    def add_constraint(self, constraint: ConstraintTemplate):
        self._constraints.add(constraint)

    def applies_to(self, constraint):
        return constraint in self._constraints

    def apply(self, constraint: ConstraintTemplate, groups: [Block], solutions):
        return constraint.source.candidates(groups, solutions, constraint.filters)


class InternalSolvingStrategy(DictSolvingStrategy):
    def __init__(self):
        super().__init__()

        def series(c: Series, assignments, solutions):
            def test_series(x_v):
                x, = to_single_vector_data(x_v)
                for i in range(len(x)):
                    if not x[i] == i + 1:
                        return False
                return True

            return self._generate_test_vectors(assignments, [c.x], test_series)

        def all_different(c: AllDifferent, assignments, solutions):
            def test_all_different(x_v):
                if not (
                    Typing.is_sub_type(x_v.type, Typing.string)
                    or Typing.is_sub_type(x_v.type, Typing.int)
                ):
                    return False

                x, = to_single_vector_data(x_v)
                seen = set()
                for i in range(len(x)):
                    if x[i] in seen:
                        return False
                    seen.add(x[i])
                return True

            return self._generate_test_vectors(assignments, [c.x], test_all_different)

        def permutation(c: Permutation, assignments, solutions):
            def test_permutation(x_v):
                x, = to_single_vector_data(x_v)
                number_set = set(range(1, len(x) + 1))

                for i in range(len(x)):
                    if not x[i] in number_set:
                        return False
                    number_set.remove(x[i])
                return len(number_set) == 0

            return self._generate_test_vectors(assignments, [c.x], test_permutation)

        def rank(c: Rank, assignments, solutions):
            # TODO Speed up by using local inconsistencies: check some random elements and check consistency of rank
            def is_rank(y_v, x_v):
                # Calculate rank values for x and compare, fail fast
                y, x = to_single_vector_data(y_v, x_v)

                # Fail-fast test:
                cutoff = min(len(y), 5)
                for i in range(cutoff):
                    if y[i] < 1 or y[i] > len(x):
                        return False

                ranked = rank_data(x)
                for i in range(0, len(ranked)):
                    if ranked[i] != y[i]:
                        return False

                # Check if not equal
                return not found_equal(y_v, x_v, solutions)

            return self._generate_test_vectors(assignments, [c.y, c.x], is_rank)

        def foreign_keys(constraint, assignments, solutions):

            pks = dict()
            for assignment in assignments:
                pk_block = assignment[constraint.pk.name]
                for pk_v in pk_block:
                    if pk_v not in pks:
                        pk, = to_single_vector_data(pk_v)
                        pks[pk_v] = set(pk)

            keys = [constraint.pk, constraint.fk]

            def test_foreign_key(pk_v, fk_v):
                blank_f = blank_filter(fk_v.data)[1]
                fk, = to_single_vector_data(fk_v)
                pk_set = pks[pk_v]
                for i in range(len(fk)):
                    if blank_f(fk[i]) and fk[i] not in pk_set:
                        return False
                return True

            return self._generate_test_vectors(assignments, keys, test_foreign_key)

        def lookups(c: Lookup, assignments, solutions):
            # TODO redundant lookups
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
                pk, pv, fk, fv = [
                    assignment[k.name] for k in [c.o_key, c.o_value, c.f_key, c.f_value]
                ]
                for pk_v, pv_v in itertools.product(pk, pv):
                    if not pk_v.overlaps_with(pv_v):
                        pk_d, pv_d = to_single_vector_data(pk_v, pv_v)
                        pk_dict = dict(zip(pk_d, pv_d))
                        for fk_v, fv_v in itertools.product(fk, fv):
                            fk_d, fv_d = to_single_vector_data(fk_v, fv_v)
                            if (
                                not (
                                    found_equal(pk_v, fk_v, solutions)
                                    and found_equal(pv_v, fv_v, solutions)
                                )
                                and not any(
                                    g1.overlaps_with(g2)
                                    for g1 in [pk_v, pv_v]
                                    for g2 in [fk_v, fv_v]
                                )
                                and not fk_v.overlaps_with(fv_v)
                                and is_lookup(pk_dict, fk_d, fv_d)
                            ):
                                result = {
                                    c.o_key: pk_v,
                                    c.o_value: pv_v,
                                    c.f_key: fk_v,
                                    c.f_value: fv_v,
                                }
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

            def test_equal(ok_v, ov_v, fk_v, fv_v):
                # Test if vectors are equal
                if (
                    found_equal(ok_v, fk_v, solutions)
                    and found_equal(ov_v, fv_v, solutions)
                    and found_equal(ok_v, ov_v, solutions)
                ):
                    return False

                ok, ov, fk, fv = to_single_vector_data(ok_v, ov_v, fk_v, fv_v)
                exact = True
                for i in range(len(fk)):
                    index = find_fuzzy(fk[i], ok)
                    if index is not None and ok[index] != fk[i]:
                        exact = False
                    if index is None or not equal(ov[index], fv[i]):
                        return False
                return (
                    not exact
                    and not found_equal(ok_v, fk_v, solutions)
                    and not found_equal(ov_v, fv_v, solutions)
                )

            return self._generate_test_vectors(assignments, keys, test_equal)

        def conditional_aggregate(
            c: ConditionalAggregate, assignments, solutions: Solutions
        ):
            partial_cache = dict()
            fk_dict = dict()

            overlap = dict()
            new_assignments = []

            # Calculate overlap
            for assignment in assignments:
                ok_block = assignment[c.o_key.name]
                fk_block = assignment[c.f_key.name]

                candidate = False
                for ok_v in ok_block:
                    for fk_v in fk_block:
                        key = frozenset({ok_v, fk_v})
                        if key not in overlap:
                            ok_d, fk_d = to_single_vector_data(ok_v, fk_v)
                            overlap[key] = len(set(ok_d) & set(fk_d)) > 0
                        if overlap[key]:
                            candidate = True

                if candidate:
                    new_assignments.append(assignment)

            assignments = new_assignments

            if isinstance(c, VirtualConditionalAggregate):
                keys = (
                    ConditionalAggregate.o_key,
                    ConditionalAggregate.f_key,
                    ConditionalAggregate.values,
                )
            else:
                keys = [c.o_key, c.f_key, c.values, c.result]

            def is_aggregate(ok, fk, v, r=None):
                if not overlap[frozenset({ok, fk})]:
                    return False

                foreign_key = ForeignKey()
                if solutions.has(
                    foreign_key, [foreign_key.fk, foreign_key.pk], [ok, fk]
                ):
                    return False

                if r is None:
                    vectors = {g: g.get_vector(1) for g in [ok, fk, v]}
                    r = "?"
                    vectors[r] = evaluate.evaluate_template(
                        c, {k: assignment[k.name].get_vector(1) for k in keys}
                    ).flatten()

                else:
                    if solutions.has(
                        foreign_key, [foreign_key.fk, foreign_key.pk], [r, v]
                    ):
                        return False

                    vectors = {g: g.vector_data[0] for g in [ok, r, fk, v]}

                for g in [ok, r, v]:
                    # FIXME avoid all call
                    if g not in partial_cache:
                        partial_cache[g] = all(
                            numpy.vectorize(blank_filter(vectors[g])[1])(vectors[g])
                        )
                    if not partial_cache[g]:
                        return False

                if fk not in fk_dict:
                    filtered = vectors[fk][
                        blank_filter(vectors[fk], True)[1](vectors[fk])
                    ]
                    unique = set(filtered)
                    masks = {u: vectors[fk] == u for u in unique}
                    fk_dict[fk] = masks

                any_match = False
                for i in range(len(vectors[ok])):
                    if vectors[ok][i] not in fk_dict[fk]:
                        res = c.default
                    else:
                        k = vectors[ok][i]
                        data = vectors[v][fk_dict[fk][k]]
                        res = (
                            c.operation.aggregate(data) if len(data) > 0 else c.default
                        )
                        any_match = True

                    n_digits = precision_and_scale(vectors[r][i])[1]
                    res = numpy.round(res, n_digits)
                    if not equal(res, vectors[r][i]):
                        return False

                    lookup = Lookup()
                    if solutions.has(
                        lookup,
                        [lookup.f_value, lookup.f_key, lookup.o_key, lookup.o_value],
                        [fk, v, r, ok],
                    ):
                        return False
                return any_match

            return self._generate_test_vectors(assignments, keys, is_aggregate)

        def are_neighbors(vec1: Block, vec2: Block):
            return vec1.vector_index() == vec2.vector_index() - 1

        def conditional_aggregate2(c: ConditionalAggregate2, assignments, _):
            agg = c.operation.aggregate

            def is_grouped_aggregate(ok1_v, ok2_v, result_v, fk1_v, fk2_v, values_v):
                if not are_neighbors(ok1_v, ok2_v) or not are_neighbors(fk1_v, fk2_v):
                    return False  # Fail because keys are not neighbors

                ok1, ok2, r, fk1, fk2, v = to_single_vector_data(ok1_v, ok2_v, result_v, fk1_v, fk2_v, values_v)
                ok_map = dict()

                for i in range(len(ok1)):
                    key = (ok1[i], ok2[i])
                    if key in ok_map:
                        return False  # Fail because ok-pairs are not unique
                    ok_map[key] = r[i]

                fk_grouped = defaultdict(list)

                for i in range(len(fk1)):
                    key = (fk1[i], fk2[i])
                    fk_grouped[key].append(v[i])

                all_keys = set(ok_map.keys()) | set(fk_grouped.keys())

                for key in all_keys:
                    if key in ok_map:
                        # If the key is in the ok_map we have to check it,
                        # otherwise it only occurs in the fk and we can ignore it (no completeness assumption)
                        res = ok_map[key]
                        if key in fk_grouped:
                            # Check that result matches with computed result
                            if not equal_smart_round(agg(fk_grouped[key], partial=False), res):
                                return False
                        else:
                            # Check that res is None, nan or 0
                            if res is not None and not numpy.isnan(res) and not equal_smart_round(0, res):
                                return False

                return True

            keys = [c.ok1, c.ok2, c.result, c.fk1, c.fk2, c.values]
            return self._generate_test_vectors(assignments, keys, is_grouped_aggregate)

        def running_total(c: RunningTotal, assignments, solutions):
            def is_running_diff(acc_v, pos_v, neg_v):
                acc_d, pos_d, neg_d = to_single_vector_data(acc_v, pos_v, neg_v)
                if not acc_d[0] == pos_d[0] - neg_d[0]:
                    return False
                for i in range(1, len(acc_d)):
                    if not equal(acc_d[i], acc_d[i - 1] + pos_d[i] - neg_d[i]):
                        return False
                if found_equal(pos_v, neg_v, solutions):
                    return False
                return True

            return self._generate_test_vectors(
                assignments, [c.acc, c.pos, c.neg], is_running_diff
            )

        def foreign_operation(c: ForeignOperation, assignments, solutions):
            keys = [c.o_key, c.f_key, c.result, c.o_value, c.f_value]

            def is_foreign_product(ok_v, fk_v, r_v, ov_v, fv_v):
                ok, fk, r, ov, fv = to_single_vector_data(ok_v, fk_v, r_v, ov_v, fv_v)
                m = dict(zip(ok, ov))
                for i in range(len(fk)):
                    if not equal(r[i], c.operation.func(fv[i], m[fk[i]])):
                        return False
                return True

            return self._generate_test_vectors(assignments, keys, is_foreign_product)

        def aggregate(
            c: Aggregate, assignments: List[Dict[str, Block]], solutions: Solutions
        ):
            results = []
            o_column = Orientation.is_vertical(c.orientation)
            projection = Projection()

            def add(solution):
                mapping = {c.x: projection.projected, c.y: projection.result}
                mapped = {mapping[v].name: solution[v.name] for v in c.variables}
                if not solutions.has_solution(projection, mapped) and not equal_groups(
                    solutions, solution
                ):
                    results.append(solution)

            for assignment in assignments:
                x_group, y_group = (
                    assignment[k.name] for k in [c.x, c.y]
                )  # type: Block
                x_data = x_group.data
                y_length = y_group.vector_length()

                o_match = Filter.orientation(x_group) == c.orientation
                if o_match:
                    sums = c.operation.aggregate(
                        x_group.data, 0 if o_column else 1, x_group.has_blanks
                    )
                    for y_vector_group in y_group:
                        y_vector_data, = to_single_vector_data(y_vector_group)
                        match = pattern_finder(sums, y_vector_data)
                        x_match = [x_group.sub_block(m, y_length) for m in match]
                        for x in x_match:
                            if not x.overlaps_with(y_vector_group):
                                add({c.x.name: x, c.y.name: y_vector_group})
                else:
                    if not o_column:
                        x_data = x_data.T

                    def check(start, end):
                        d1, d2 = x_data.shape
                        y_vector = y_group.vector_data[y_i]
                        for i in range(0, d2):
                            result = c.operation.aggregate(
                                x_data[start:end, i], 0, x_group.has_blanks
                            )
                            if not equal_v(result, y_vector.data[i]).all():
                                return False
                        x_subgroup = x_group.sub_block(start, end - start)
                        y_subgroup = y_group.sub_block(y_i, 1)
                        add({c.x.name: x_subgroup, c.y.name: y_subgroup})
                        return True

                    max_range = MaxRange(check)
                    for y_i in range(y_group.vector_count()):
                        if y_group == x_group:
                            max_range.find(0, y_i, c.min_vectors)
                            max_range.find(
                                y_i + 1, x_group.vector_count(), c.min_vectors
                            )
                        else:
                            max_range.find(0, x_group.vector_count(), c.min_vectors)

            return results

        def product(c: Product, assignments, solutions):
            keys = [c.result, c.first, c.second]

            # cache = set()

            def is_product(r_v, o1_v, o2_v):
                if not ordered(o1_v, o2_v):
                    return False

                r, o1, o2 = to_single_vector_data(r_v, o1_v, o2_v)
                for i in range(0, len(r)):
                    if r_v > o2_v:
                        expected = r[i]
                        actual = Operation.PRODUCT.func(o1[i], o2[i])
                    elif o1[i] != 0:
                        expected = o2[i]
                        actual = r[i] / o1[i]
                    else:
                        return False
                    res = smart_round(actual, expected)
                    if not equal(expected, res):
                        return False

                # Caching relies on the order of the assignments being the same as the group ordering
                # cache.add((r_v, o1_v, o2_v))
                return True

            return self._generate_test_vectors(assignments, keys, is_product)

        def diff(c: Diff, assignments, solutions):
            def is_diff(r_v, o1_v, o2_v):
                if not (o2_v < r_v):
                    return False

                r, o1, o2 = to_single_vector_data(r_v, o1_v, o2_v)
                for i in range(0, len(r)):
                    if not equal(r[i], o1[i] - o2[i]):
                        return False
                return all(not equal_v(v, 0).all() for v in (r, o1, o2))

            keys = [c.result, c.first, c.second]
            return self._generate_test_vectors(assignments, keys, is_diff)

        def percent_diff(c: PercentualDiff, assignments, solutions):
            def is_diff(r_v, o1_v, o2_v):
                r, o1, o2 = (v.get_vector(1) for v in (r_v, o1_v, o2_v))
                for i in range(0, len(r)):
                    if o2[i] == 0:
                        return False
                    res = (o1[i] - o2[i]) / o2[i]
                    n_digits = precision_and_scale(r[i])[1]
                    res = numpy.round(res, n_digits)
                    if o2[i] == 0 or not equal(r[i], res):
                        return False
                if found_equal(o1_v, o2_v, solutions):
                    return False
                return True

            keys = [c.result, c.first, c.second]
            return self._generate_test_vectors(assignments, keys, is_diff)

        def sum_product(c: Product, assignments, solutions):
            keys = [c.result, c.first, c.second]

            def is_sum_product(r_v, o1_v, o2_v):
                if not ordered(o1_v, o2_v) or r_v.rows() != 1 or r_v.columns() != 1:
                    return False

                r, o1, o2 = to_single_vector_data(r_v, o1_v, o2_v)

                # TODO too many vector operations (easy)
                return equal_v(
                    r, numpy.sum(numpy.vectorize(Operation.PRODUCT.func)(o1, o2))
                ).all()

            return self._generate_test_vectors(assignments, keys, is_sum_product)

        def project(c: Projection, assignments, _):
            solutions = []
            masks = {}
            size = 2

            for assignment in assignments:
                r_group, p_group = [assignment[v.name] for v in [c.result, c.projected]]  # type: Block
                if p_group not in masks:
                    bool_mask = numpy.vectorize(blank_filter(p_group.data)[1])(
                        p_group.data
                    )
                    masks[p_group] = numpy.vectorize(lambda e: 1 if e else 0)(bool_mask)
                p_masked = masks[p_group] if p_group.orientation == Orientation.horizontal else masks[p_group].T

                def check(start, end):
                    result = numpy.sum(p_masked[start:end, :], 0)
                    if numpy.vectorize(lambda e: e == 1)(result).all():
                        p_subgroup = p_group.sub_block(start, end - start)
                        p_data = (
                            p_subgroup.data if p_subgroup.orientation == Orientation.horizontal else p_subgroup.data.T
                        )
                        if equal_v(
                            r_group.vector(r_i),
                            Operation.SUM.aggregate(p_data, 0),
                        ).all():
                            r_subgroup = r_group.sub_block(r_i, 1)
                            solutions.append(
                                {
                                    c.result.name: r_subgroup,
                                    c.projected.name: p_subgroup,
                                }
                            )
                        return True
                    return False

                max_range = MaxRange(check)
                for r_i in range(r_group.vector_count()):
                    if r_group == p_group:
                        max_range.find(0, r_i, size)
                        max_range.find(r_i + 1, p_group.vector_count(), size)
                    else:
                        max_range.find(0, p_group.vector_count(), size)
            return solutions

        def equality(c: Equal, assignments, _):
            equal_map = dict()

            def test(x_v, y_v):
                # Only compare in order
                if not ordered(x_v, y_v):
                    return False

                # Check transitivity (both are equal to a third)
                if (
                    x_v in equal_map
                    and y_v in equal_map
                    and equal_map[x_v] == equal_map[y_v]
                ):
                    return True

                # Test element-wise, fail fast
                x, y = to_single_vector_data(x_v, y_v)
                for i in range(0, len(x)):
                    if not equal(x[i], y[i]):
                        return False

                # Equal vectors, update cache:
                if y_v in equal_map:
                    found = equal_map[y_v]
                    minimal, maximal = (x_v, found) if x_v < found else (found, x_v)
                    equal_map[y_v] = minimal
                    equal_map[maximal] = minimal
                else:
                    equal_map[y_v] = x_v
                return True

            return self._generate_test_vectors(assignments, [c.first, c.second], test)

        def equal_group(c: EqualGroup, assignments, solutions: Solutions):
            result = []
            for assignment in assignments:
                x = assignment[c.x.name]

                def test(start, end):
                    solution = {c.x.name: x.vector_subset(start + 1, end)}
                    if equal_groups(solutions, solution):
                        result.append(solution)
                        return True
                    return False

                max_range = MaxRange(test)
                max_range.find(0, x.vectors(), 2)
            return result

        def ordered_constraint(c: Ordered, assignments, solutions):
            def test_ordering(x_v):
                x, = to_single_vector_data(x_v)
                for i in range(1, len(x)):
                    if x[i] <= x[i - 1]:
                        return False
                return True

            return self._generate_test_vectors(assignments, [c.x], test_ordering)

        def xor_vector(c: MutualExclusiveVector, assignments, solutions):
            return self._generate_test_vectors(
                assignments, [c.x], lambda xb: c.test_data(*to_single_vector_data(xb))
            )

        def xor(c, assignments: List[Dict[str, Block]], solutions):
            result = []

            for assignment in assignments:
                x = assignment[c.x.name]

                def test(start, end):
                    block = x.sub_block(start, end - start)
                    solution = {c.x.name: block}

                    if c.test_data(block.data):
                        result.append(solution)
                        return True
                    return False

                max_range = MaxRange(test)
                max_range.find(0, x.vector_count(), 2)

            return result

        def virtual_lookups(template, assignments, solutions):
            # type: (ConstraintTemplate, List[Dict[str, Group]], Solutions) -> List[Dict[str, Group]]

            results = []

            for assignment in assignments:
                pk, pv, fk = [
                    assignment[k.name]
                    for k in [Lookup.o_key, Lookup.o_value, Lookup.f_key]
                ]
                for pk_v, pv_v in itertools.product(pk, pv):
                    if not pk_v.overlaps_with(pv_v):
                        for fk_v in fk:
                            if not found_equal(pk_v, fk_v, solutions) and not any(
                                g1.overlaps_with(g2)
                                for g1 in [pk_v, pv_v]
                                for g2 in [fk_v]
                            ):
                                result = {
                                    Lookup.o_key: pk_v,
                                    Lookup.o_value: pv_v,
                                    Lookup.f_key: fk_v,
                                }
                                results.append({k.name: v for k, v in result.items()})

            return results

        def grouped_aggregate(c: GroupedAggregate, assignments, _):

            def is_grouped_aggregate(k1_v, k2_v, v_v):
                i1 = k1_v.relative_range.vector_index(k1_v.orientation)
                i2 = k2_v.relative_range.vector_index(k2_v.orientation)
                if i1 != i2 - 1:
                    return False
                k1, k2, v = to_single_vector_data(k1_v, k2_v, v_v)
                grouped = defaultdict(list)
                for i in range(len(k1)):
                    key = (k1[i], k2[i])
                    grouped[key].append(v[i])
                for val in grouped.values():
                    if not equal(smart_round(c.operation.aggregate(numpy.array(val[:-1]), partial=False), val[-1]), val[-1]):
                        return False
                return True

            keys = [c.k1, c.k2, c.v]
            return self._generate_test_vectors(assignments, keys, is_grouped_aggregate)

        self.add_strategy(Equal(), equality)
        # self.add_strategy(EqualGroup(), equal_group)
        self.add_strategy(Series(), series)
        self.add_strategy(AllDifferent(), all_different)
        self.add_strategy(Permutation(), permutation)
        self.add_strategy(Rank(), rank)
        self.add_strategy(ForeignKey(), foreign_keys)
        # self.add_strategy(VirtualLookup(), virtual_lookups)
        self.add_strategy(Lookup(), lookups)
        # self.add_strategy(FuzzyLookup(), fuzzy_lookup)
        for c_instance in ConditionalAggregate.instances():
            self.add_strategy(c_instance, conditional_aggregate)
        for c_instance in ConditionalAggregate2.instances():
            self.add_strategy(c_instance, conditional_aggregate2)
        # for c_instance in VirtualConditionalAggregate.instances():
        #     self.add_strategy(c_instance, conditional_aggregate)
        self.add_strategy(RunningTotal(), running_total)
        # self.add_strategy(ForeignProduct(), foreign_operation)
        self.add_strategy(Projection(), project)
        for c_instance in Aggregate.instances():
            self.add_strategy(c_instance, aggregate)
        self.add_strategy(Product(), product)
        self.add_strategy(Diff(), diff)
        # self.add_strategy(PercentualDiff(), percent_diff)
        self.add_strategy(SumProduct(), sum_product)
        self.add_strategy(Ordered(), ordered_constraint)
        for c in MutualExclusivity.instances():
            self.add_strategy(c, xor)
        self.add_strategy(MutualExclusiveVector(), xor_vector)
        for c_instance in GroupedAggregate.instances():
            self.add_strategy(c_instance, grouped_aggregate)

    @staticmethod
    def _generate_test_vectors(assignments, keys, test_groups):
        # FIXME Improve code by avoiding to test overlapping subgroups multiple times
        for assignment in assignments:
            for vectors in itertools.product(*[assignment[k.name] for k in keys]):
                if not any(
                    g1.overlaps_with(g2)
                    for g1, g2 in itertools.combinations(vectors, 2)
                ) and (test_groups is None or test_groups(*vectors)):
                    yield dict(zip([k.name for k in keys], vectors))


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


def equal(x, y, scale=False):
    if x is None or y is None:
        return x is y
    if (
        isinstance(x, (float, int))
        and isinstance(y, (float, int))
        and (isinstance(x, float) or isinstance(y, float))
    ):
        delta = pow(10, -10)
        if scale:
            n_digits = min(precision_and_scale(x)[1], precision_and_scale(y)[1])
            x = numpy.round(x, n_digits)
            y = numpy.round(y, n_digits)
        return (numpy.isnan(x) and numpy.isnan(y)) or abs(x - y) < delta
    else:
        return x == y


def equal_smart_round(computed, expected):
    if computed is None or expected is None:
        return computed is expected

    if numpy.isnan(computed) and numpy.isnan(expected):
        return True

    delta = pow(10, -10)
    return abs(smart_round(computed, expected) - expected) < delta


@functools.lru_cache(maxsize=None)
def precision_and_scale(x):
    max_digits = 14
    int_part = int(abs(x))
    magnitude = 1 if int_part == 0 else int(math.log10(int_part)) + 1
    if magnitude >= max_digits:
        return magnitude, 0
    frac_part = abs(x) - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    scale = int(math.log10(frac_digits))
    return magnitude + scale, scale


def smart_round(number, reference):
    n_digits = precision_and_scale(reference)[1]
    return numpy.round(number, n_digits)


equal_v = numpy.vectorize(equal)


def pattern_finder(source, pattern):
    matches = []
    if len(pattern) > len(source):
        return matches
    for i in range(len(source) - len(pattern) + 1):
        if (
            equal(source[i], pattern[0])
            and numpy.vectorize(equal)(source[i : i + len(pattern)], pattern).all()
        ):
            matches.append(i)
    return matches


def ordered(*args):
    if len(args) <= 1:
        return True
    for i in range(1, len(args)):
        if args[i] < args[i - 1]:
            return False
    return True


def to_vector_groups(*args):
    for arg in args:
        for g_v in arg:
            yield g_v


def equal_groups(solutions, solution):
    vector_set = to_vector_groups(*solution.values())
    sols = itertools.combinations(sorted(vector_set), 2)
    equal_c = Equal()
    sols = [{equal_c.first.name: v1, equal_c.second.name: v2} for (v1, v2) in sols]
    return all(solutions.has_solution(equal_c, sol) for sol in sols)


def to_vector_data(*args):
    for arg in args:  # type: Block
        for i in range(arg.vector_count()):
            yield arg.vector_data[i]


def to_single_vector_data(*args):
    for arg in args:  # type: Block
        assert arg.vector_count() == 1
        yield arg.vector_data[0]


def complete(vector):
    _, blank_f = blank_filter(vector)
    if not blank_f(vector[0]):
        return False
    for i in range(1, len(vector)):
        if not blank_f(vector[i]):
            vector[i] = vector[i - 1]
    return vector


def found_equal(v1, v2, solutions):
    eq = Equal()
    keys = [eq.first, eq.second]
    return (
        solutions.has(eq, keys, (v1, v2))
        if v1 < v2
        else solutions.has(eq, keys, (v2, v1))
    )
