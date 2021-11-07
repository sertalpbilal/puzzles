import sasoptpy as so
from pathlib import Path
import os

def solve_sudoku(fixed):

    # Initialize model
    model = so.Model(name='sudoku')

    # Define sets
    rows = list(range(1,10))
    cols = list(range(1,10))
    values = list(range(1,10))

    # Define variables
    assign = model.add_variables(rows, cols, values, vartype=so.binary, name='assign')
    
    # Add constraints

    ## Fixed values
    model.add_constraints((assign[r,c,v] == 1 for (r,c,v) in fixed), name='fixed_assignment')

    ## Row + value pairs
    model.add_constraints((so.expr_sum(assign[r,c,v] for c in cols) == 1 for r in rows for v in values), name='row_value_pair')
    ## Col + value pairs
    model.add_constraints((so.expr_sum(assign[r,c,v] for r in rows) == 1 for c in cols for v in values), name='col_value_pair')
    ## Row + col pairs
    model.add_constraints((so.expr_sum(assign[r,c,v] for v in values) == 1 for r in rows for c in cols), name='row_col_pair')

    ## 3x3 blocks
    blocks = [
        [
            (i,j)
            for i in range(3*row_block+1, 3*(row_block+1)+1)
            for j in range(3*col_block+1, 3*(col_block+1)+1)
        ]
        for row_block in range(3) for col_block in range(3)
    ]

    for no, members in enumerate(blocks):
        model.add_constraints((so.expr_sum(assign[r,c,v] for (r,c) in members) == 1 for v in values), name=f'block_pair_{no+1}')

    # Define objective
    model.set_objective(0, sense='N', name='empty_obj')

    # Export
    tmp_dir = Path() / "tmp"
    tmp_dir.mkdir(exist_ok=True, parents=True)
    model.export_mps(tmp_dir / "sudoku.mps")

    # Solve
    os.system("cbc tmp/sudoku.mps solve solu tmp/sudoku_soln.txt")

    # Read solution
    with open('tmp/sudoku_soln.txt', 'r') as f:
        for line in f:
            if 'Infeasible' in line:
                print('Problem is infeasible')
                return
            if 'objective value' in line:
                continue
            words = line.split()
            var = model.get_variable(words[1])
            var.set_value(float(words[2]))

    # Print value
    solution = []
    print("Solution")
    for r in rows:
        for c in cols:
            for v in values:
                if assign[r,c,v].get_value() > 0.5:
                    print(v, end=' ')
                    solution.append([r,c,v])
        print('')

    return solution

if __name__ == "__main__":
    solve_sudoku([
        (1,2,5),
        (1,3,8),
        (1,7,2),
        (2,1,6),
        (2,3,7),
        (2,4,2),
        (3,1,3),
        (3,4,4),
        (4,3,5),
        (5,1,9),
        (5,3,6),
        (6,2,3),
        (6,6,4),
        (7,1,1),
        (7,3,9),
        (7,9,4),
        (8,5,4),
        (8,7,6),
        (8,8,7),
        (9,1,8)
    ])
