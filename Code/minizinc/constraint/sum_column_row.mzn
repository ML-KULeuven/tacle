include "layout.mzn";

var 1..y_vectors: y_selected;                       % selected vector in the y-group
var 1..x_rows: x_start;   % start of the x-group selection
var 1..x_rows: x_end;   % end of the x-group selection

constraint x_end > x_start;
constraint x_columns = y_length;

% make sure that the groups don't overlap if they are the same
%constraint is_same_group -> (G1_sel < G2_start \/ G2_start+L12-1 < G1_sel);



% columnwise sum over array that represent columns
constraint
  forall(i in 1..y_length) (
    % not valid: y_data[y_selected, i] = sum(j in x_start..x_end) (x_data[j, i])
    y_data[y_selected, i] = sum(j in 1..x_rows) ( (j in x_start..x_end)*(x_data[j, i]) )
  );

output ["X["++show(x_start)++":"++show(x_end)++"]\n"++
        "Y["++show(y_selected)++":"++show(y_selected)++"]\n"];

solve satisfy;
