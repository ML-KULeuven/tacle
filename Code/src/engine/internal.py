import itertools

import math

from core.constraint import *
from core.group import Group
from core.solutions import Solutions
from core.strategy import AssignmentStrategy, DictSolvingStrategy


class MaxRange:
    def __init__(self, test: callable):
        self._test = test

    def find(self, start, end, size, limit=None, last=None):
        limit = start + size - 1 if limit is None else limit
        last = end if last is None else last
        self._find(start, end, size, limit, last)

    def _find(self, start, end, size, limit, last):
        if last - start < size:
            pass
        elif end - start < size or end <= limit:
            self._find(start + 1, last, size, max(start + size, limit), last)
        else:
            if self._test(start, end):
                self._find(start + 1, last, size, end, last)
            else:
                self._find(start, end - 1, size, limit, last)


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
        self.add_constraint(Lookup())
        self.add_constraint(FuzzyLookup())
        for c in ConditionalAggregate.instances():
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

    def add_constraint(self, constraint: Constraint):
        self._constraints.add(constraint)

    def applies_to(self, constraint):
        return constraint in self._constraints

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
                blank_f = blank_filter(fk_group.data, vectorized=True)[1]
                fk_sets = map(lambda v: (v, set(filter(blank_f, v.get_vector(1)))), fk_vectors)

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
                if not all(all(numpy.vectorize(blank_filter(v)[1])(v)) for v in [ok_v, r_v, v_v]):
                    return False
                blank_f = blank_filter(fk_v)[1]
                if not blank_f(fk_v[0]):
                    return False
                m = dict(zip(ok_v, range(len(ok_v))))
                acc = [None] * len(r_v)
                for i in range(len(fk_v)):
                    if blank_f(fk_v[i]):
                        key = m[fk_v[i]]
                        aggregated = c.operation.aggregate(v_v[i])
                        acc[key] = aggregated if acc[key] is None else c.operation.func(acc[key], aggregated)
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
                    if not equal(r[i], c.operation.func(fv[i], m[fk[i]])):
                        return False
                return True

            return self._generate_test_vectors(assignments, keys, is_foreign_product)

        def aggregate(c: Aggregate, assignments: List[Dict[str, Group]], solutions: Solutions):
            results = []
            o_column = Orientation.column(c.orientation)
            operation_f = c.operation.aggregate
            projection = Projection()

            def add(solution):
                mapping = {c.x: projection.projected, c.y: projection.result}
                mapped = {mapping[v].name: solution[v.name] for v in c.variables}
                if not solutions.has_solution(projection, mapped) and not equal_groups(solutions, solution):
                    results.append(solution)

            for assignment in assignments:
                x_group, y_group = (assignment[k.name] for k in [c.x, c.y])
                x_data = x_group.data
                assert isinstance(x_group, Group)
                assert isinstance(y_group, Group)
                y_length = y_group.length()

                o_match = x_group.row == Orientation.row(c.orientation)
                if o_match:
                    sums = operation_f(x_group.data, 0 if o_column else 1)
                    for y_vector_group in y_group:
                        match = pattern_finder(sums, y_vector_group.get_vector(1))
                        x_match = [x_group.vector_subset(m + 1, m + y_length) for m in match]
                        for x in x_match:
                            if not x.overlaps_with(y_vector_group):
                                add({c.x.name: x, c.y.name: y_vector_group})
                else:
                    if not o_column:
                        x_data = x_data.T

                    def check(start, end):
                        result = operation_f(x_data[start:end, :], 0)
                        if equal_v(result, y_group.get_vector(y_i + 1)).all():
                            x_subgroup = x_group.vector_subset(start + 1, end)
                            y_subgroup = y_group.vector_subset(y_i + 1, y_i + 1)
                            add({c.x.name: x_subgroup, c.y.name: y_subgroup})
                            return True
                        return False

                    max_range = MaxRange(check)
                    for y_i in range(y_group.vectors()):
                        if y_group == x_group:
                            max_range.find(0, y_i, 2)
                            max_range.find(y_i + 1, x_group.vectors(), 2)
                        else:
                            max_range.find(0, x_group.vectors(), 2)

            return results

        def product(c: Product, assignments, solutions):
            keys = [c.result, c.first, c.second]

            def is_product(r, o1, o2):
                return numpy.vectorize(equal)(r, numpy.vectorize(Operation.PRODUCT.func)(o1, o2)).all()

            return self._generate_test_vectors(assignments, keys, is_product, lambda r, o1, o2: ordered(o1, o2))

        def diff(c: Diff, assignments, solutions):
            def is_diff(r, o1, o2):
                return numpy.vectorize(equal)(r, o1 - o2).all()

            keys = [c.result, c.first, c.second]
            return self._generate_test_vectors(assignments, keys, is_diff, lambda r, _, o2: o2 < r)

        def percent_diff(c: PercentualDiff, assignments, solutions):
            def is_diff(r, o1, o2):
                if equal_v(o2, 0).any():
                    return False
                calculated = (o1 - o2) / o2
                equal_t = numpy.vectorize(lambda x, y: equal(x, y, True))
                return equal_t(r, calculated).all()

            keys = [c.result, c.first, c.second]
            return self._generate_test_vectors(assignments, keys, is_diff)

        def sum_product(c: Product, assignments, solutions):
            keys = [c.result, c.first, c.second]

            def is_sum_product(r, o1, o2):
                return numpy.vectorize(equal)(r, numpy.sum(numpy.vectorize(Operation.PRODUCT.func)(o1, o2))).all()

            return self._generate_test_vectors(assignments, keys, is_sum_product, lambda r, o1, o2: ordered(o1, o2))

        def project(c: Projection, assignments, _):
            solutions = []
            masks = {}
            size = 2

            for assignment in assignments:
                r_group, p_group = [assignment[v.name] for v in [c.result, c.projected]]
                if p_group not in masks:
                    bool_mask = numpy.vectorize(blank_filter(p_group.data)[1])(p_group.data)
                    masks[p_group] = numpy.vectorize(lambda e: 1 if e else 0)(bool_mask)
                p_masked = masks[p_group] if p_group.row else masks[p_group].T

                def check(start, end):
                    result = numpy.sum(p_masked[start:end, :], 0)
                    if numpy.vectorize(lambda e: e == 1)(result).all():
                        p_subgroup = p_group.vector_subset(start + 1, end)
                        p_data = p_subgroup.data if p_subgroup.row else p_subgroup.data.T
                        if equal_v(r_group.get_vector(r_i + 1), Operation.SUM.aggregate(p_data, 0)).all():
                            r_subgroup = r_group.vector_subset(r_i + 1, r_i + 1)
                            solutions.append({c.result.name: r_subgroup, c.projected.name: p_subgroup})
                        return True
                    return False

                max_range = MaxRange(check)
                for r_i in range(r_group.vectors()):
                    if r_group == p_group:
                        max_range.find(0, r_i, size)
                        max_range.find(r_i + 1, p_group.vectors(), size)
                    else:
                        max_range.find(0, p_group.vectors(), size)
            return solutions

        def equality(c: Equal, assignments, _):
            test = lambda x, y: equal_v(x, y).all()
            return self._generate_test_vectors(assignments, [c.first, c.second], test, ordered)

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

        self.add_strategy(Equal(), equality)
        self.add_strategy(EqualGroup(), equal_group)
        self.add_strategy(Series(), series)
        self.add_strategy(AllDifferent(), all_different)
        self.add_strategy(Permutation(), permutation)
        self.add_strategy(Rank(), rank)
        self.add_strategy(ForeignKey(), foreign_keys)
        self.add_strategy(Lookup(), lookups)
        self.add_strategy(FuzzyLookup(), fuzzy_lookup)
        for c_instance in ConditionalAggregate.instances():
            self.add_strategy(c_instance, conditional_aggregate)
        self.add_strategy(RunningTotal(), running_total)
        self.add_strategy(ForeignProduct(), foreign_operation)
        self.add_strategy(Projection(), project)
        for c_instance in Aggregate.instances():
            self.add_strategy(c_instance, aggregate)
        self.add_strategy(Product(), product)
        self.add_strategy(Diff(), diff)
        self.add_strategy(PercentualDiff(), percent_diff)
        self.add_strategy(SumProduct(), sum_product)

    @staticmethod
    def _generate_test_vectors(assignments, keys, test_vectors, test_groups=None):
        for assignment in assignments:
            for vectors in itertools.product(*[assignment[k.name] for k in keys]):
                if not any(g1.overlaps_with(g2) for g1, g2 in itertools.combinations(vectors, 2)) \
                        and (test_groups is None or test_groups(*vectors)) \
                        and test_vectors(*list(map(lambda vec: vec.get_vector(1), vectors))):
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
    if isinstance(x, float) or isinstance(y, float):
        delta = pow(10, -10)
        if scale:
            n_digits = min(precision_and_scale(x)[1], precision_and_scale(y)[1])
            x = numpy.round(x, n_digits)
            y = numpy.round(y, n_digits)
        return (numpy.isnan(x) and numpy.isnan(y)) or abs(x - y) < delta
    else:
        return x == y


def precision_and_scale(x):
    max_digits = 14
    int_part = int(abs(x))
    magnitude = 1 if int_part == 0 else int(math.log10(int_part)) + 1
    if magnitude >= max_digits:
        return (magnitude, 0)
    frac_part = abs(x) - int_part
    multiplier = 10 ** (max_digits - magnitude)
    frac_digits = multiplier + int(multiplier * frac_part + 0.5)
    while frac_digits % 10 == 0:
        frac_digits /= 10
    scale = int(math.log10(frac_digits))
    return magnitude + scale, scale


equal_v = numpy.vectorize(equal)


def pattern_finder(source, pattern):
    matches = []
    if len(pattern) > len(source):
        return matches
    for i in range(len(source) - len(pattern) + 1):
        if equal(source[i], pattern[0]) and numpy.vectorize(equal)(source[i:i + len(pattern)], pattern).all():
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


def complete(vector):
    _, blank_f = blank_filter(vector)
    if not blank_f(vector[0]):
        return False
    for i in range(1, len(vector)):
        if not blank_f(vector[i]):
            vector[i] = vector[i - 1]
    return vector
