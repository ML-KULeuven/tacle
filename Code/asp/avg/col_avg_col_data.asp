1 { shift(X)      : range(X)   } 1. % shift takes one value from 0 to N
1 { selected_Y(V) : rel_Y(_,V) } 1.

y_vector(Py+ShiftY,Wy) :- selected_Y(Vy), element_Y(Vy,Py,Wy), shift(ShiftY).

sum_x(Pos,Vala)   :- Vala = #sum{X,P: element_X(Vx,P,X) }, rel_X(Pos,Vx).
count_x(Pos,Valb) :- Valb = #count{P: element_X(Vx,P,_)}, rel_X(Pos,Vx).
avg_x(Pos,Val)    :- Val = Vala/Valb, sum_x(Pos,Vala), count_x(Pos,Valb).

holds(Py) :- y_vector(Py,Wy), avg_x(Py,Wy).

:- y_vector(Py, _), not holds(Py).

#show avg_x/2.
#show y_vector/2.
#show selected_Y/1.
#show holds/1.
#show shift/1.
