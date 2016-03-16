rel_X(1,vx1).  rel_X(2,vx2).  rel_X(3,vx3). 
rel_Y(1,vy1).  rel_Y(2,vy2). 

element_Y(vy1,1,14). element_Y(vy1,2,15). element_Y(vy1,3,18). element_Y(vy1,4,21).
element_Y(vy2,1,7).  element_Y(vy2,2,10). element_Y(vy2,3,8).  element_Y(vy2,4,21).  

element_X(vx1,1,7).  element_X(vx1,2,8).  element_X(vx1,3,9). element_X(vx1,4,10).
element_X(vx2,1,7).  element_X(vx2,2,7).  element_X(vx2,3,9). element_X(vx2,4,11).
element_X(vx3,1,1).  element_X(vx3,2,1).  element_X(vx3,3,1). element_X(vx3,4,1).

1 { selected_Y(V) : rel_Y(_,V) } 1.
0 { selected_X(V)} 1 :-  rel_X(_,V) .

:- selected_Y(V), selected_X(V).

y_vector(Py,Wy) :- selected_Y(Vy), element_Y(Vy,Py,Wy).

sum_X(Pos,Val) :- Val = #sum{X,V: element_X(V,Pos,X), selected_X(V) }, y_vector(Pos,_).

holds(Py) :- y_vector(Py,Wy), sum_X(Py,Wy).

:- y_vector(Py, _), not holds(Py).

#show sum_X/2.
#show y_vector/2.
#show selected_Y/1.
#show selected_X/1.
#show holds/1.
