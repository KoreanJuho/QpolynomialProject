import numpy as np
import os

# Create model
def create_sag_function(terms):
    def sag_function(r, *params):
        result = 0
        for i, term in enumerate(terms):
            result += params[i] * r ** term
        return result
    return sag_function

# Curve fitting function
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
    
    for _ in range(100):
        J = jacobian(r, z, func, params)
        E = z - func(r, *params)
        if sum(E**2)/len(E) >= 0.01:
            step = 10
        elif sum(E**2)/len(E) >= 1e-4:
            step = 0.01
        elif sum(E**2)/len(E) >= 1e-6:
            step = 0.001
        else:
            step = 0
        
        if sum(E**2)/len(E) <= 1e-10:
            break
        params = params - np.linalg.pinv(J.T @ J + step * np.diag(J.T @ J)) @ (J.T @ E)

    E = sum((z - func(r, *params))**2)
    
    return params, E

# get r,z value
def get_rz():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    file_path = r"../SAG.txt"

    with open(file_path, 'r') as file:
        lines = file.readlines()
        data = [list(map(float, line.strip().split())) for line in lines[1:]]
        file.close()

    r = np.array([row[0] for row in data])
    z = np.array([row[1] for row in data])
    return r,z

r, z = get_rz()
terms = [4, 6, 8, 10, 12, 14, 16, 18, 20]
params = []

for weight, term in enumerate(terms):
    params = np.append(params, 0)
    sag_function = create_sag_function(terms[0:len(params)])
    params, E = Curve_fit(sag_function, r, z, params)
    print(E)
    if term == 20:
        break

surface = 2
letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J']
asp_params = ''.join([f'{letters[i]} s{surface} {param:.6e}; ' for i, param in enumerate(params)])
myasp = f"asp s{surface};{asp_params}set vig"
print(E)
print(myasp)