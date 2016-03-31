1 { start(X) : range(X) } 1.
1 { end(X)   : range(X) } 1.

:- start(S), end(S).

selected_X(V) :-  rel_X(Pos,V), start(S0), end(S1), Pos >= S0, Pos <= S1.

1 { selected_Y(V) : rel_Y(_,V) } 1.

y_vector(Py,Wy) :- selected_Y(Vy), element_Y(Vy,Py,Wy).

x_min(Pos,Val) :- Val = #min{ W,V: element_X(V,Pos,W), selected_X(V) }, y_vector(Pos,_).

:- selected_Y(V), selected_X(V).

holds(Pos) :- x_min(Pos,Val), y_vector(Pos,Val).

:- y_vector(Pos,_), not holds(Pos).

#minimize{1,V:selected_X(V)}.

#show selected_Y/1.
#show selected_X/1.
#show start/1.
#show end/1.
#show x_min/2.
#show holds/1.
