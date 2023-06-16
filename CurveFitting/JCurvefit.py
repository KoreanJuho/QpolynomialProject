import numpy as np
import os

def Curve_fit(func, r, z, params):
    
    def jacobian(r, z, func, params):
        m = len(z)
        n = len(params)
        jacobian_matrix = np.zeros((m, n))
        for i in range(m):
            for j in range(n):
                E1 = z[i]- func(r[i], *params)
                dx = params.copy()
                dx[j] += 0.001
                E2 = z[i]- func(r[i], *dx)
                jacobian_matrix[i][j] = (E2-E1)/0.001
        return jacobian_matrix
    
    for _ in range(10):
        J = jacobian(r, z, func, params)
        E = z - func(r, *params)
        params = params - np.linalg.pinv(J.T @ J) @ (J.T @ E)

    E = sum((z - func(r, *params))**2)
    
    return params, E

# get r,z value
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
file_path = r"../SAG.txt"

with open(file_path, 'r') as file:
    lines = file.readlines()
    data = [list(map(float, line.strip().split())) for line in lines[1:]]
    file.close()

r = np.array([row[0] for row in data])
z = np.array([row[1] for row in data])

# create model
def create_sag_function(terms):
    def sag_function(r, *params):
        result = 0
        for i, term in enumerate(terms):
            result += params[i] * r ** term
        return result
    return sag_function

terms = [4, 6, 8, 10, 12, 14, 16, 18, 20]
params = [0, 0, 0, 0]

sag_function = create_sag_function(terms[0:len(params)])

params, E = Curve_fit(sag_function, r, z, params)

surface = 2
myasp = f"asp s{surface};A s{surface} {params[0]:.6e};B s{surface} {params[1]:.6e};C s{surface} {params[2]:.6e};D s{surface} {params[3]:.6e};set vig"
print(E)
print(myasp)