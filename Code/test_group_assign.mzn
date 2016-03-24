%%% groups
int: nG = 7;
array [1..nG] of int: g_length = [4, 4, 4, 4, 4, 5, 4];
array [1..nG] of int: g_columns = [1, 1, 6, 1, 2, 5, 5];
array [1..nG] of int: g_rows = [4, 4, 4, 4, 4, 4, 4];
array [1..nG] of bool: g_numeric = [true, false, true, false, true, true, true];
array [1..nG] of bool: g_row_orientation = [false, false, false, false, false, true, false];

%%% variables
int: nV = 2;
array [1..nV] of bool: v_numeric = [true, true];
array [1..nV] of bool: v_vector = [false, true];

array [1..nV] of var int: assign;

%%% constraints
constraint (not g_row_orientation[assign[1]] )-> g_length[assign[2]] <= g_columns[assign[1]];
constraint g_row_orientation[assign[1]] -> g_length[assign[2]] = g_columns[assign[1]];
constraint g_rows[assign[1]] > 1;

constraint forall(v in 1..nV)(v_numeric[v] -> g_numeric[assign[v]]);

solve satisfy;
