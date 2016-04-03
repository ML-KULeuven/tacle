# Direct implementations for the internal engine
class AssignmentGenerator:
    def __init__(self, constraint: Constraint):
        self.constraint = constraint

    def generate(self, groups, solutions):
        for assignment in self.constraint.source.candidates(groups, solutions, self.constraint.filters):
            if all([f.test(assignment) for f in self.constraint.filters]):
                yield assignment
            else:
                raise Exception("!!!!!", [([str(v) for v in f.variables], f.test(assignment)) for f in self.constraint.filters])


        def series(constraint, groups, solutions):
            a2 = list([{constraint.get_variables()[0].name: g} for g in filter(Group.is_integer, groups)])
            print(list(generate_assignments(constraint, groups, solutions)))
            print(a2)
            return a2

        def all_different(constraint, groups, solutions):
            a2 = [{constraint.get_variables()[0].name: g} for g in filter(Group.is_textual, groups)]
            print(list(generate_assignments(constraint, groups, solutions)))
            print(a2)
            return a2

        def permutation(constraint, groups, solutions):
            a2 = [{constraint.get_variables()[0].name: g} for g in filter(Group.is_integer, groups)]
            print(list(generate_assignments(constraint, groups, solutions)))
            print(a2)
            return a2

        def rank(constraint, groups, solutions):
            assignments = []
            for y_group in solutions.get_property_groups(Permutation()):
                for x_group in filter(Group.is_numeric, groups):
                    if x_group.length() == y_group.length():
                        assignments.append({"Y": y_group, "X": x_group})

            print(list(generate_assignments(constraint, groups, solutions)))
            print(assignments)

            return assignments

        def foreign_keys(constraint, groups, solutions):
            assignments = []
            for pk_group in solutions.get_property_groups(AllDifferent()):
                for fk_group in filter(Group.is_textual, groups):
                    if not pk_group.is_subgroup(fk_group):
                        assignments.append({constraint.pk.name: pk_group, constraint.fk.name: fk_group})
            print(list(generate_assignments(constraint, groups, solutions)))
            print(assignments)
            return assignments

        def lookups(c: Lookup, groups, solutions):
            assignments = []
            foreign_key = ForeignKey()
            for solution in solutions.get_solutions(foreign_key):
                pk, fk = [solution[key] for key in [foreign_key.pk.name, foreign_key.fk.name]]
                pv_filter = lambda g: g.length() == pk.length() and g.table == pk.table and g.row == pk.row
                pv_candidates = list(filter(pv_filter, groups))
                fv_filter = lambda g: g.length() == fk.length() and g.table == fk.table and g.row == fk.row
                fv_candidates = list(filter(fv_filter, groups))
                assignments += [{c.o_key.name: pk, c.f_key.name: fk, c.o_value.name: pv, c.f_value.name: fv}
                                for pv in pv_candidates for fv in fv_candidates]

            print(list(generate_assignments(c, groups, solutions)))
            print(assignments)
            return assignments

        self.add_strategy(Series(), series)
        self.add_strategy(AllDifferent(), all_different)
        self.add_strategy(Permutation(), permutation)
        self.add_strategy(Rank(), rank)
        self.add_strategy(ForeignKey(), foreign_keys)
        self.add_strategy(Lookup(), lookups)

        ## Complex generate test


            @staticmethod
    def _test(assignments, keys, test_f):
        for assignment in assignments:
            yield from InternalSolvingStrategy._generate_test_vectors_rec(assignment, [k if isinstance(k, tuple) else ([k], lambda x: x.get_vector(1)) for k in keys], {}, [], test_f)

    @staticmethod
    def _generate_test_vectors_rec(assignment, keys, vectors, inputs, test_f):
        if len(keys) == 0:
            if test_f(*inputs):
                yield(vectors)
        else:
            (key_set, transformer) = keys[0]
            for choices in itertools.product(*[assignment[k.name] for k in key_set]):
                if not any(g1.overlaps_with(g2) for g1, g2 in itertools.combinations(list(vectors.values()) + list(choices), 2)):
                    new_vectors = {k: v for k, v in vectors.items()}
                    for k, v in zip(key_set, choices):
                        new_vectors[k.name] = v
                    new_inputs = inputs + [transformer(*choices)]
                    yield from InternalSolvingStrategy._generate_test_vectors_rec(assignment, keys[1:], new_vectors, new_inputs, test_f)