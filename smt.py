from z3 import *
import numpy as np
import time, datetime
import argparse
import collections

def read_txt(filename):
    n = 0
    paper_shape = []
    gift_shape = []
    input_file = open(filename,'r')
    i = 0
    for line in input_file:
        if i > 1:
            i += 1
            line = line.strip().split(' ')
            if len(line) < 2:
                break
            gift_shape.append([int(e) for e in line])
        if i == 1:
            i += 1
            line = line.strip()
            n = int(line)
        if i == 0:
            i += 1
            line = line.strip().split(' ')
            paper_shape = [int(e) for e in line]
    input_file.close()
    return n, paper_shape, gift_shape

parser = argparse.ArgumentParser(description='Present Wrapping Problem SMT solver')
parser.add_argument('input_file', help='input instance file in txt format')
parser.add_argument('--save_file','-o', default=False, action='store_true',help='save file with solution')
parser.add_argument('--rotate','-r', default=False, action='store_true', help='allow the rotation of each piece')
args = parser.parse_args()

print(args.input_file, args.save_file, args.rotate)

filename = args.input_file
save_file = args.save_file
rotation_enabled = args.rotate

n, paper_shape, gift_shape = read_txt(filename)
print(n, paper_shape, gift_shape)

# If the gift can be rotated and the rotation is enabled, invert the two coordinates Else keep them as they are
# Done that, add to the model the constraints: 0 <= the position of the gift 
#                                              position of the gift <= dimension of paper - dimension of the shape
def paper_constraints(s):
    gift_pos = []
    gift_rot = []
    gift_rot_shape = []
    for i in range(n):
        gift_pos.append((Int('x'+str(i)), Int('y'+str(i))))
        gift_rot.append(Bool('r'+str(i)))
        gift_rot_shape.append([0,0])
        for j in range(2):
            gift_rot_shape[i][j] = If(And(gift_rot[i], rotation_enabled), gift_shape[i][1-j], gift_shape[i][j])
            s.add(0 <= gift_pos[i][j], gift_pos[i][j] <= paper_shape[j] - gift_rot_shape[i][j])
    return s, gift_pos, gift_rot, gift_rot_shape

# This function adds the constraint: If  (position of the gift <= dimension of the paper) & (the same position + the rotated shape > dimension of the paper)
#                                    Then add to dimension sum the rotated dimension of the gift, else add 0
#                                    The sum of every dimension sum has to be lesser or equal than the dimension of the paper
# In other words, this checks that every row and column contains only gifts that, summed over the vertical or horizontal dimension, 
# do not exceed the dimension of the paper
def implied_constraints(s, gift_pos, gift_rot, gift_rot_shape):
    for k in (0,1):
        for j in range(paper_shape[k]):
            dimension_sum = []
            for i in range(n):
                inc = If(And(gift_pos[i][k] <= j, gift_pos[i][k] + gift_rot_shape[i][k] > j),
                            gift_rot_shape[i][1-k], 0)
                dimension_sum.append(inc)
            s.add(sum(dimension_sum) <= paper_shape[k])
    return s

# This function add the constraint: Given two gifts, they cannot overlap
def non_overlap(s, gift_pos, gift_rot, gift_rot_shape):
    for i in range(n):
        for j in range(i): 
            s.add(Or(gift_pos[j][0] >= gift_pos[i][0] + gift_rot_shape[i][0],
                     gift_pos[j][0] + gift_rot_shape[j][0] <= gift_pos[i][0],
                     gift_pos[j][1] >= gift_pos[i][1] + gift_rot_shape[i][1],
                     gift_pos[j][1] + gift_rot_shape[j][1] <= gift_pos[i][1]))
    return s, gift_pos, gift_rot, gift_rot_shape

# Print the solution in the terminal
def print_grid(positions):
    for i in range(paper_shape[0]):
        row = ''
        for j in range(paper_shape[1]):
            if positions[j,paper_shape[0]-i-1] == 1:
                row += "# "
            elif positions[j,paper_shape[0]-i-1] == 0:
                row += ". "
            else:
                row += 'o '
        print(row)
    print()

start = time.time()
s = Solver()

s, gift_pos, gift_rot, gift_rot_shape = paper_constraints(s)
s, gift_pos, gift_rot, gift_rot_shape = non_overlap(s, gift_pos, gift_rot, gift_rot_shape)
s = implied_constraints(s, gift_pos, gift_rot, gift_rot_shape)
print("Compiled in:", time.time()-start)
print("Model Check")
start = time.time()
s.check()
print("solved in:", time.time()-start)
#for k, v in s.statistics():
#    print(k, v)

m = s.model()
solution = []
rotated = {}

for d in sorted(m.decls(), key=lambda x: (int(x.name()[1:]), x.name()[0])):
    if isinstance(m[d], BoolRef) == False:
        solution.append(m[d].as_long())
    else:
        rotated[d.name()] =  'Rotated' + str(m[d])
for i in range(n):
    rot_key = 'r'+str(i)
    if rot_key not in rotated.keys():
        if rotation_enabled:
            rotated[rot_key] = 'Square'
        else:
            rotated[rot_key] = 'Rotation Disabled'

solution = [[solution[i*2], solution[i*2+1]] for i in range(len(solution)//2)]
rotated = collections.OrderedDict(sorted(rotated.items()))
rotation_ls = []
if rotation_enabled:
    for i, y in rotated.items():
        if y == 'RotatedTrue':
            k = int(i.replace('r', ''))
            plch = gift_shape[k][0]
            gift_shape[k][0] = gift_shape[k][1] 
            gift_shape[k][1] = plch
        rotation_ls.append((i, y))
print("Solution:",solution)
print("Shapes:  ", gift_shape)
print("Rotations: ", rotation_ls)
print()

positions = np.zeros((n, paper_shape[0], paper_shape[1]), dtype=int)

for i,s in enumerate(solution):
    positions[i, s[0]:s[0] + gift_shape[i][0], s[1]:s[1] + gift_shape[i][1]] = 1

if save_file:
    fileout = filename.strip('.txt')+'-out.txt'
    if rotation_enabled:
        fileout = fileout.strip('.txt')+'-rot.txt'
    with open(fileout,'w') as f:
        f.write(str(paper_shape[0])+' '+str(paper_shape[1])+'\n')
        f.write(str(n)+'\n')
        for shape, sol in zip(gift_shape,solution):
            f.write(f"{shape[0]} {shape[1]}\t{sol[0]} {sol[1]}\n")

print('The solution visualization is:')
print('Legend:')
print('. - Empty', '# - Occupied', 'o - Overlap', sep = '\n')
print_grid(np.sum(positions, axis = 0))
