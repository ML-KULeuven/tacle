from constraint import Constraint
from parser import Group
from asp_python import ASPConstraintVisitor


def find_constraints(constraint: Constraint, assignments: [{Group}]):
  asp_visitor = ASPConstraintVisitor(assignments)	
  output      = asp_visitor.visit(constraint)
  return output


