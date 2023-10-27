import pandas as pd

def reblock_model(block_model, original_dim, reblock_dim):
    # original block model dimensions
    dx, dy, dz = map(int, original_dim)

    # set original coordinates to block origin
    block_model['X'] -= dx / 2
    block_model['Y'] -= dy / 2
    block_model['Z'] -= dz / 2

    # reblocked model dimensions
    rdx, rdy, rdz = map(int, reblock_dim)

    # calculate the block coordinates in the new grid
    block_model['rx'] = (block_model['X'] // rdx) * rdx
    block_model['ry'] = (block_model['Y'] // rdy) * rdy
    block_model['rz'] = (block_model['Z'] // rdz) * rdz

    # set reblocked coordinates to block centroid
    block_model['rx'] += rdx / 2
    block_model['ry'] += rdy / 2
    block_model['rz'] += rdz / 2

    # Group by the reblocked coordinates and calculate reblocked values for each block in each column
    reblocked_model = block_model.groupby(['rx', 'ry', 'rz']).agg({
        **{column: 'sum'
           for column in block_model if column[0] == '$' or column[0] == '+'},
        **{column: 'mean'
           for column in block_model if column[0] == '%'},
        **{column: lambda x: (x * block_model.loc[x.index, '%Density']).sum() / block_model.loc[x.index, '%Density'].sum()
           for column in block_model if column[0] == '@' or column[0] == '/'}
    }).reset_index()
    # rename reblocked coordinates
    reblocked_model.rename(columns={'rx': 'X', 'ry': 'Y', 'rz': 'Z'}, inplace=True)
    return reblocked_model

input_file = input("Enter the original file path \n")
output_file = input("Enter the output file path \n")
original_dimensions = input("Enter the values for the original x, y, z dimensions. format: 0 0 0 \n").split()
reblock_dimensions = input("Enter the values for the relocked x, y, z dimensions. format: 0 0 0 \n").split()
block_model = pd.read_csv(input_file)
reblocked_model = reblock_model(block_model, original_dimensions, reblock_dimensions)
reblocked_model.to_csv(output_file, index=False)