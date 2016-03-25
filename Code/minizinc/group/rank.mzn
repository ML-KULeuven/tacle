constraint forall(i in 1..nV) (g_length[assign[i]] > 1);
constraint g_length[assign[1]] = g_length[assign[2]];
constraint forall(v in 1..nV)(v_numeric[v] -> g_numeric[assign[v]]);
