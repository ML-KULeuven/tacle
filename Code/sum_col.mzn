array [1..L11,1..L12] of int: G1;
int: L11;
int: L12;
array [1..L21,1..L22] of int: G2;
int: L21;
int: L22;
bool: is_same_group;

var 1..L11: G1_sel;             % the column ID of  T1
var 1..(L21-L12+1): G2_start;   % start in G2, can result in shorter than L12

% if G1 and G2 from same group: constraint that G1 not in G2
constraint is_same_group -> (G1_sel < G2_start \/ G2_start+L12-1 < G1_sel);

% columnwise sum over array that represent columns
constraint
  forall(i in 1..L12) (
    G1[G1_sel,i] = sum(j in 1..L22) (G2[(G2_start+i-1),j])
  );

solve satisfy;
