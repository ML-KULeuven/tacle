from constraint import Constraint
from engine import Engine
from parser import Group


def find_constraints(engine: Engine, constraint: Constraint, assignments: [{Group}], solutions):
	return engine.find_constraints(constraint, assignments, solutions)
