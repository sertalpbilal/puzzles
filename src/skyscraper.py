import sasoptpy as so
from pathlib import Path
import os
import itertools
import time

def solve_skyscraper(N, directions):
    # Can solve small sizes pretty fast

    # N is the size of square
    # directions: list of entries
    # e.g. "top", 3, 2 means: from top to bottom, 3rd column, value is 2
    #      "right", 1, 5 means: from right to left, 1st row, value is 5
    #      "fixed", 1, 1, 2 means: row 1, column 1 cell value is 2

    # Define model
    model = so.Model(name='skyscraper')

    # Add variables

    values = range(1,N+1)
    rows = range(1,N+1)
    cols = range(1,N+1)
    assign = model.add_variables(rows, cols, values, vartype=so.binary, name='assign')

    # Add constraints

    ## each row + value
    model.add_constraints((so.expr_sum(assign[r,c,v] for c in cols) == 1 for r in rows for v in values), name='row_value_pair')

    ## each col + value
    model.add_constraints((so.expr_sum(assign[r,c,v] for r in rows) == 1 for c in cols for v in values), name='col_value_pair')

    ## each row + col
    model.add_constraints((so.expr_sum(assign[r,c,v] for v in values) == 1 for r in rows for c in cols), name='row_col_pair')

    ## pre-process skyscrapers
    # score_dict = {}
    perm = list(itertools.permutations(range(1,N+1)))
    perm_indices = list(range(len(perm)))
    regular_scores = []
    reverse_scores = []
    for p in perm:
        current_value = 0
        score = 0
        for i in p:
            if i > current_value:
                score+=1
                current_value=i
        regular_scores.append(score)
        current_value = 0
        score = 0
        for i in reversed(p):
            if i > current_value:
                score+=1
                current_value=i
        reverse_scores.append(score)

    row_perm = model.add_variables(rows, perm_indices, vartype=so.binary, name='row_perm')
    col_perm = model.add_variables(cols, perm_indices, vartype=so.binary, name='col_perm')
    
    ## each row/col should be one of perm
    model.add_constraints((so.expr_sum(row_perm[r, p] for p in perm_indices) == 1 for r in rows), name='row_perm_pair')
    model.add_constraints((so.expr_sum(col_perm[c, p] for p in perm_indices) == 1 for c in cols), name='col_perm_pair')
    ## connect assign and perm
    model.add_constraints((so.expr_sum(assign[r,c,perm[p][c-1]]  for c in cols) >= N * row_perm[r, p] for r in rows for p in perm_indices), name='assign_row_perm_con')
    model.add_constraints((so.expr_sum(assign[r,c,perm[p][r-1]]  for r in rows) >= N * col_perm[c, p] for c in cols for p in perm_indices), name='assign_col_perm_con')

    for d_no, d in enumerate(directions):
        t = d[1]
        v = d[2]
        if d[0] == "top":
            possible_permutations = [p for p in perm_indices if regular_scores[p] == v]
            model.add_constraint(so.expr_sum(col_perm[t,p] for p in possible_permutations) == 1, name=f'given_{d_no}')
        elif d[0] == "bottom":
            possible_permutations = [p for p in perm_indices if reverse_scores[p] == v]
            model.add_constraint(so.expr_sum(col_perm[t,p] for p in possible_permutations) == 1, name=f'given_{d_no}')
        elif d[0] == "left":
            possible_permutations = [p for p in perm_indices if regular_scores[p] == v]
            model.add_constraint(so.expr_sum(row_perm[t,p] for p in possible_permutations) == 1, name=f'given_{d_no}')
        elif d[0] == "right":
            possible_permutations = [p for p in perm_indices if reverse_scores[p] == v]
            model.add_constraint(so.expr_sum(row_perm[t,p] for p in possible_permutations) == 1, name=f'given_{d_no}')
        elif d[0] == "fixed":
            r = d[1]
            c = d[2]
            v = d[3]
            model.add_constraint(assign[r,c,v] == 1, name=f'given_{d_no}')

    # Empty objective
    model.set_objective(0, sense='N', name='empty_obj')

    # Export and solve
    tmp = Path("tmp")
    tmp.mkdir(parents=True, exist_ok=True)
    model.export_mps(tmp / "skyscraper.mps")
    os.system("cbc tmp/skyscraper.mps solve solu tmp/skyscraper_soln.txt")

    # Read solution
    with open(f'tmp/skyscraper_soln.txt', 'r') as f:
        for line in f:
            if 'Infeasible' in line or 'infeasible' in line:
                print("Problem is infeasible!")
                return
            if 'objective value' in line:
                continue
            words = line.split()
            var = model.get_variable(words[1])
            var.set_value(float(words[2]))

    # Print values
    print("Solution")
    # Print top directions
    print('   ', end='')
    for c in cols:
        for d in directions:
            if d[0] == 'top' and d[1] == c:
                print(d[2], end='')
                break
        else:
            print(' ', end='')
        print(' ', end='')
    print('')
    print('   ' + '-'*(2*N-1))

    for r in rows:
        # left direction
        for d in directions:
            if d[0] == 'left' and d[1] == r:
                print(d[2], end='| ')
                break
        else:
            print(' | ', end='')
        # values
        for c in cols:
            for v in values:
                if assign[r,c,v].get_value() > 0.5:
                    print(v, end=' ')
        # right direction
        for d in directions:
            if d[0] == 'right' and d[1] == r:
                print('|' + str(d[2]))
                break
        else:
            print('|')

    # Print bottom directions
    print('   ' + '-'*(2*N-1))
    print('   ', end='')
    for c in cols:
        for d in directions:
            if d[0] == 'bottom' and d[1] == c:
                print(d[2], end='')
                break
        else:
            print(' ', end='')
        print(' ', end='')
    print('')

    time.sleep(0.5)
    os.unlink("tmp/skyscraper.mps")
    os.unlink("tmp/skyscraper_soln.txt")

if __name__ == "__main__":
    solve_skyscraper(5, [
        ("top", 1, 3),
        ("top", 2, 4),
        ("left", 2, 5),
        ("right", 3, 3),
        ("bottom", 4, 4),
        ("bottom", 5, 2)
    ])
