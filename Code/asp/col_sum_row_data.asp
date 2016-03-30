1 { start(X) : range(X) } 1.
1 { end(X)   : range(X) } 1.

:- start(S), end(S).

1 { selected_Y(V) : rel_Y(_,V) } 1.
selected_X(V) :-  rel_X(Pos,V), start(S0), end(S1), Pos >= S0, Pos <= S1.

:- selected_Y(V), selected_X(V).

y_vector(Py,Wy) :- selected_Y(Vy), element_Y(Vy,Py,Wy).

sum_X(Pos,Val) :- Val = #sum{X,V: element_X(V,Pos,X), selected_X(V) }, y_vector(Pos,_).

holds(Py) :- y_vector(Py,Wy), sum_X(Py,Wy).

:- y_vector(Py, _), not holds(Py).

#show sum_X/2.
#show start/1.
#show end/1.
#show y_vector/2.
#show selected_Y/1.
#show selected_X/1.
#show holds/1.
