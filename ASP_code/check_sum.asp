rel_X(1,vx1).  rel_X(2,vx2).  rel_X(3,vx3).  rel_X(4,vx4). rel_X(5,vx5). rel_X(6,vx6). rel_X(7,vx7).  
rel_Y(1,vy1).  rel_Y(2,vy2). 

element_Y(vy1,1,991). element_Y(vy1,2,1030). element_Y(vy1,3,1046). element_Y(vy1,4,1081). element_Y(vy1,5,4148).
element_Y(vy2,2,370). element_Y(vy2,2,408).  element_Y(vy2,3,396).  element_Y(vy2,4,387).  element_Y(vy2,5,1551).

element_X(vx1,1,1).   element_X(vx1,2,2).    element_X(vx1,3,3).   element_X(vx1,4,4).
element_X(vx2,1,353). element_X(vx2,2,370).  element_X(vx2,3,175). element_X(vx2,4,93).
element_X(vx3,1,378). element_X(vx3,2,408).  element_X(vx3,3,146). element_X(vx3,4,98).
element_X(vx4,1,396). element_X(vx4,2,387).  element_X(vx4,3,167). element_X(vx4,4,96).
element_X(vx5,1,387). element_X(vx5,2,386).  element_X(vx5,3,203). element_X(vx5,4,105).
element_X(vx6,1,1514).element_X(vx6,2,1551). element_X(vx6,3,691). element_X(vx6,4,392).
element_X(vx7,1,2).   element_X(vx7,2,1).    element_X(vx7,3,3).   element_X(vx7,4,4).

range(0..7).


1 { shift(X)      : range(X)   } 1. % shift takes one value from 0 to N
1 { selected_Y(V) : rel_Y(_,V) } 1.

y_vector(Py+ShiftY,Wy) :- selected_Y(Vy), element_Y(Vy,Py,Wy), shift(ShiftY).

sum_X(Pos,Vx,Val) :- Val = #sum{X: element_X(Vx,P,X) }, rel_X(Pos,Vx).

holds(Py) :- y_vector(Py,Wy), sum_X(Py,_,Wy).

:- y_vector(Py, _), not holds(Py).

#show sum_X/3.
#show y_vector/2.
#show selected_Y/1.
#show holds/1.
#show shift/1.
