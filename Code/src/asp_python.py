from constraint import ConstraintVisitor, SumColumn

class ASPConstraintVisitor(ConstraintVisitor):

  def __init__(self, assignments):
    self.assignments = assignments

  def visit_sum_column(self, constraint: SumColumn):
    for xy_dict in self.assignments:
      X = xy_dict["X"]
      Y = xy_dict["Y"]
    # generate_and_check(X,Y)
      if X.row == False:
          solutions = self.handle_sum_column_data_in_column(X,Y)
  
  @staticmethod
  def yid(idint):
    return "vy"+str(idint)

  def handle_sum_column_data_in_column(self,X,Y):
    Ydata = Y.get_group_data()
    print("Y", Ydata)
    if Y.row == False:
      Ydata = Ydata.T

    for i,vs in enumerate(Ydata):
      print("rel_Y({pos},{vid}).".format(pos=i,vid=self.yid(i)), end=" ")
      for j,v in enumerate(vs):
          print("element_Y({vid},{pos},{val})".format(vid=self.yid(i),pos=j,val=v), end=" ")
      print(" ")
          
    

    max_shift = X.bounds.columns() - Y.length()
    
    print("max_shift:", max_shift)

    
    



     


