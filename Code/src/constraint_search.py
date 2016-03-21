from constraint import Constraint
from engine import Engine
from parser import Group


def find_constraints(engine: Engine, constraint: Constraint, assignments: [{Group}]):
	# asp_visitor = ASPConstraintVisitor(assignments)
	# output      = asp_visitor.visit(constraint)
	return engine.find_constraints(constraint, assignments)
