int: x_columns;
int: x_rows;

int: y_vectors;
int: y_length;

array [1..x_rows, 1..x_columns] of float: x_data;
array [1..y_vectors, 1..y_length] of float: y_data;

bool: is_same_group;

var 1..y_vectors: y_selected;                       % selected vector in the y-group
var 1..(x_columns - y_length + 1): x_start;   % start of the x-group selection

% make sure that the groups don't overlap if they are the same
%constraint is_same_group -> (G1_sel < G2_start \/ G2_start+L12-1 < G1_sel);

% columnwise sum over array that represent columns
constraint
  forall(i in 1..y_length) (
    y_data[y_selected, i] = sum(j in 1..x_rows) (x_data[j, (x_start + i - 1)])
  );

solve satisfy;
