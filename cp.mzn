include "globals.mzn";

% To start, please open the instance to be solved in MiniZinc

array[1..2] of int: paper_shape;
int: n;
array[1..n,1..2] of int: present_shape;

% Each gift is represented by its bottom-left corner
array[1..n,1..2] of var 0..max(paper_shape): present_position;

array[1..n] of var bool: rotations = [false | i in 1..n]; 
function var int : present_rotation(int: i, int: j) = 
  if rotations[i] then present_shape[i, 3-j] 
  else present_shape[i,j] endif;

% Gifts cannot overlap
constraint diffn(present_position[1..n,1], 
                 present_position[1..n,2], 
                [present_rotation(i,1) | i in 1..n], 
                [present_rotation(i,2) | i in 1..n]);

% Gifts cannot fall over the border of the paper
constraint forall(i in 1..n)(
  present_position[i,1] <= paper_shape[1] - present_rotation(i,1) 
);

constraint forall(i in 1..n)(
  present_position[i,2] <= paper_shape[2] - present_rotation(i,2) 
);
% The sum of every gift's y-dimension in each row has to be equal to the y-dimension of the paper 
constraint cumulative(present_position[1..n,1],
                      [present_rotation(i,1) | i in 1..n],
                      [present_rotation(i,2) | i in 1..n],
                      paper_shape[2]);
                      
% The sum of every gift's x-dimension in each row has to be equal to the x-dimension of the paper             
constraint cumulative(present_position[1..n,2],
                      [present_rotation(i,2) | i in 1..n],
                      [present_rotation(i,1) | i in 1..n],
                      paper_shape[1]);
                      
% Constraint the first gift to be in the upper-left corner of the paper
%constraint present_position[1,1] <= (paper_shape[1] - present_rotation(1,1)) / 2;  
%constraint present_position[1,2] <= (paper_shape[2] - present_rotation(1,2)) / 2;  

% To solve the problem we use the int_seach builtin MiniZinc
% As variable choice annotation we use first_fail
% To constraint the variables we use indomain_min
% This choice was made based on various tests performed using different combinations
%ann: y_search;
%y_search = int_search(present_position[1..n,2], first_fail, indomain_min);

% Comment the next line and uncomment the following three to execute this program on an instance not in the project's set of instances
%solve :: y_search satisfy;

ann: search;
search = int_search(present_position[1..n,1..2], first_fail, indomain_min);
solve :: search satisfy;

%I was not able to produce a grid output similar to the one in the Python script

output [show(paper_shape[1]) ++ " " ++ show(paper_shape[2]) ++ "\n"];
output [show(n) ++ "\n"];
output[show(present_shape[i,1]) ++ " " ++ show(present_shape[i,2]) ++" " ++ show(present_position[i,1]) ++ " " ++ show(present_position[i,2]) ++ "\n" | i in 1..n ];