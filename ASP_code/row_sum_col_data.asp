rel_X(1,vx2). rel_X(2,vx3). rel_X(3,vx4). rel_X(4,vx5). rel_X(5,vx6). rel_X(6,vx7).
rel_Y(1,vx2). rel_Y(2,vx3). rel_Y(3,vx4). rel_Y(4,vx5). rel_Y(5,vx6). rel_Y(6,vx7).

element_X(vx2,1,353). element_X(vx2,2,370).  element_X(vx2,3,175). element_X(vx2,4,93).
element_X(vx3,1,378). element_X(vx3,2,408).  element_X(vx3,3,146). element_X(vx3,4,98).
element_X(vx4,1,396). element_X(vx4,2,387).  element_X(vx4,3,167). element_X(vx4,4,96).
element_X(vx5,1,387). element_X(vx5,2,386).  element_X(vx5,3,203). element_X(vx5,4,105).
element_X(vx6,1,1514).element_X(vx6,2,1551). element_X(vx6,3,691). element_X(vx6,4,392).
element_X(vx7,1,2).   element_X(vx7,2,1).    element_X(vx7,3,3).   element_X(vx7,4,4).

element_Y(vx2,1,353). element_Y(vx2,2,370).  element_Y(vx2,3,175). element_Y(vx2,4,93).
element_Y(vx3,1,378). element_Y(vx3,2,408).  element_Y(vx3,3,146). element_Y(vx3,4,98).
element_Y(vx4,1,396). element_Y(vx4,2,387).  element_Y(vx4,3,167). element_Y(vx4,4,96).
element_Y(vx5,1,387). element_Y(vx5,2,386).  element_Y(vx5,3,203). element_Y(vx5,4,105).
element_Y(vx6,1,1514).element_Y(vx6,2,1551). element_Y(vx6,3,691). element_Y(vx6,4,392).
element_Y(vx7,1,2).   element_Y(vx7,2,1).    element_Y(vx7,3,3).   element_Y(vx7,4,4).

1 { selected_Y(V) : rel_Y(_,V) } 1.
{ selected_X(V) } :- rel_X(_,V).

y_vector(Py,Wy) :- selected_Y(Vy), element_Y(Vy,Py,Wy).

x_sum(Pos,Val) :- Val = #sum{ W,V: element_X(V,Pos,W), selected_X(V) }, y_vector(Pos,_).

:- selected_Y(V), selected_X(V).

holds(Pos) :- x_sum(Pos,Val), y_vector(Pos,Val).

:- y_vector(Pos,_), not holds(Pos).

#show selected_Y/1.
#show selected_X/1.
#show x_sum/2.
#show holds/1.
