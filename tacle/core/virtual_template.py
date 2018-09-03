from tacle.core.assignment import ConstraintSource, SameLength, NotPartial, SameTable, SameOrientation, Not, SameType
from tacle.core.template import Lookup, ForeignKey, ConstraintTemplate, Equal, ConditionalAggregate, AllDifferent


def is_virtual(template):
    #  type: (ConstraintTemplate) -> bool
    return isinstance(template, VirtualLookup) or isinstance(template, VirtualConditionalAggregate)


class VirtualLookup(Lookup):
    def __init__(self):
        variables = [self.o_key, self.o_value, self.f_key]
        source = ConstraintSource(variables, ForeignKey(), {"PK": "OK", "FK": "FK"})
        filters = [NotPartial(variables), SameLength([self.o_key, self.o_value]), SameTable([self.o_key, self.o_value]),
                   SameOrientation([self.o_key, self.o_value])]
        ConstraintTemplate.__init__(self, "virtual-lookup", "? = LOOKUP({FK}, {OK}, {OV})", source, filters, {Equal()})


class VirtualConditionalAggregate(ConditionalAggregate):
    def __init__(self, operation, default=0):
        self._default = default
        self._operation = operation
        name = operation.name
        variables = [self.o_key, self.f_key, self.values]
        # source = ConstraintSource(variables, ForeignKey(), {"PK": self.o_key, "FK": self.f_key})
        source = ConstraintSource(variables, AllDifferent(), {AllDifferent.x.name: self.o_key})
        filters = [SameLength([self.f_key, self.values]),
                   SameTable([self.f_key, self.values]), Not(SameTable([self.f_key, self.o_key])),
                   # SameTable([self.o_key, self.result]),  # TODO think about this
                   NotPartial([self.o_key]), SameType([self.f_key, self.o_key]),
                   SameOrientation([self.f_key, self.values])]
        p_format = "? = " + name.upper() + "IF({FK}={OK}, {V})"
        ConstraintTemplate.__init__(self, "virtual-{}-if".format(name.lower()), p_format, source, filters, {Lookup()})

    @classmethod
    def instance(cls, operation):
        return VirtualConditionalAggregate(operation)
