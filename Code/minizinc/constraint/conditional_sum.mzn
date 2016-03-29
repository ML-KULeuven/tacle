int: ok_vectors;
int: ok_length;
array [1..ok_vectors, 1..ok_length] of string: ok_data;

int: r_vectors;
int: r_length;
array [1..r_vectors, 1..r_length] of float: r_data;

int: fk_vectors;
int: fk_length;
array [1..fk_vectors, 1..fk_length] of string: fk_data;

int: v_vectors;
int: v_length;
array [1..v_vectors, 1..v_length] of float: v_data;

var 1..ok_vectors: ok_selected;
var 1..r_vectors: r_selected;
var 1..fk_vectors: fk_selected;
var 1..v_vectors: v_selected;

constraint
  forall(i in 1..r_length) (
    r_data[r_selected, i] = sum(j in 1..v_length) (
        (ok_data[ok_selected, i] = fk_data[fk_selected, 1]) * (v_data[v_selected, 1])
       )
  );

solve satisfy;
