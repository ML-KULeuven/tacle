%%% data
%int maxNum = 100;
int: nG = 7;
array [1..nG] of int: g_length = [4, 4, 4, 4, 4, 5, 4];
array [1..nG] of int: g_columns = [1, 1, 6, 1, 2, 5, 5];
array [1..nG] of int: g_rows = [4, 4, 4, 4, 4, 4, 4];
array [1..nG] of bool: g_numeric = [true, false, true, false, true, true, true];
% numeric = {X; Y}
bool: x_numeric = true;
bool: y_numeric = true;
% vector = {Y}
bool: x_vector = false;
bool: y_vector = true;


%%% vars, should be an array to to ease x_numeric etc
var 1..nG: X;
var 1..nG: Y;


%%% constraints Theory TVar
constraint g_length[Y] <= g_columns[X];
constraint g_rows[X] > 1;

%%% constraints Theory TGen
constraint x_numeric -> g_numeric[X];
constraint y_numeric -> g_numeric[Y];
constraint x_vector -> (g_rows[X] >= 1 \/ g_columns[X] >= 1);
constraint y_vector -> (g_rows[Y] >= 1 \/ g_columns[Y] >= 1);

solve satisfy;
