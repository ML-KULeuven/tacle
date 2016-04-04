1 { shift(X)      : range(X)   } 1. % shift takes one value from 0 to N
1 { selected_Y(V) : rel_Y(_,V) } 1.

y_vector(Py+ShiftY,Wy) :- selected_Y(Vy), element_Y(Vy,Py,Wy), shift(ShiftY).

sum_X(Pos,Vx,Val) :- Val = #sum{X,P: element_X(Vx,P,X) }, rel_X(Pos,Vx).

holds(Py) :- y_vector(Py,Wy), sum_X(Py,_,Wy).

:- y_vector(Py, _), not holds(Py).

#show sum_X/3.
#show y_vector/2.
#show selected_Y/1.
#show holds/1.
#show shift/1.
