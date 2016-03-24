constraint not g_row_orientation[assign[1]] -> g_length[assign[2]] = g_rows[assign[1]];
constraint g_row_orientation[assign[1]] -> g_length[assign[2]] <= g_rows[assign[1]];
constraint g_columns[assign[1]] > 1;
constraint forall(v in 1..nV)(v_numeric[v] -> g_numeric[assign[v]]);
