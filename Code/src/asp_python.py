from constraint import ConstraintVisitor, SumColumn
from group import GType
import numpy as np
import sh
from os import system

class ASPConstraintVisitor(ConstraintVisitor):

  def __init__(self, assignments):
    self.assignments = assignments

  def visit_sum_column(self, constraint: SumColumn):
    for i,xy_dict in enumerate(self.assignments):
      X = xy_dict["X"]
      Y = xy_dict["Y"]
    # generate_and_check(X,Y)
      if X.row == False:
          self.handle_sum_column_data_in_column(X,Y,i)
  
  @staticmethod
  def yid(idint):
    return "vy"+str(idint)

  @staticmethod
  def xid(idint):
    return "vx"+str(idint)

  @staticmethod
  def generate_Y_asp(Ydata,idfun,test_file):
    for i,vs in enumerate(Ydata):
      print("rel_Y({pos},{vid}).".format(pos=i,vid=idfun(i)), end=" ", file=test_file)
      for j,v in enumerate(vs):
          print("element_Y({vid},{pos},{val}).".format(vid=idfun(i),pos=j,val=int(v)), end=" ", file=test_file)
      print(" ",file=test_file)
   
  @staticmethod
  def generate_X_asp(Xdata,idfun,test_file):
    for i,vs in enumerate(Xdata):
      print("rel_X({pos},{vid}).".format(pos=i,vid=idfun(i)), end=" ", file=test_file)
      for j,v in enumerate(vs):
          print("element_X({vid},{pos},{val}).".format(vid=idfun(i),pos=j,val=int(v)), end=" ", file=test_file)
      print(" ",file=test_file)

  def handle_sum_column_data_in_column(self,X,Y,i):
    tmp_filename = "tmp/asp_tmp{i}.asp".format(i=i)
    print(tmp_filename)
    test_file = open(tmp_filename,"w")
    Xdata = X.get_group_data()
    Ydata = Y.get_group_data()
    if Y.row == False:
      Ydata = Ydata.T

    if Y.dtype == GType.float or X.dtype == GType.float:
        Ydata = 100*Ydata.astype(np.float32)
        Xdata = 100*Xdata.astype(np.float32)
        Ydata = Ydata.astype(int)
        Xdata = Xdata.astype(int)


    self.generate_Y_asp(Ydata,self.yid,test_file)
    self.generate_X_asp(Xdata,self.xid,test_file)


    max_shift = X.bounds.columns() - Y.length()
    
    print("range(0..{max_shift}).".format(max_shift=max_shift), file=test_file)

    test_file.close()

    system("clingo {tmp_filename} asp/check_sum.asp 0".format(tmp_filename=tmp_filename))



    
    



     


