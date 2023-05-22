import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import numpy as np
import win32com.client
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog

def browse_file():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(filetypes=[("Sequence files", "*.seq"), ("All files", "*.*")])
    return file_path

def get_surface_number():
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    surface_number = simpledialog.askinteger("Surface Number", "Which surface want to fit?")
    return surface_number

file_path = browse_file()

surface = get_surface_number()

mypth = f"run {file_path};GO"
mysur = f"in C:CVUSER\\Juho_Macro\\rsag.seq {surface}"

CV = win32com.client.Dispatch('CODEV.Command.202203_SR1')
CV.SetStartingDirectory("C:\CVUSER")
CV.StartCodeV()

CV.Command(mypth);
CV.Command(mysur);

file_path = 'C:\\CVUSER\\sag.txt'

with open(file_path, 'r') as file:
    lines = file.readlines()
    data = [list(map(float, line.strip().split())) for line in lines[1:]]
    file.close()

r = np.array([row[0] for row in data])
z = np.array([row[1] for row in data])

del file_path, lines, data, file

def create_sag_function(terms):
    def sag_function(r, *params):
        result = params[0]*r**2/(1+np.sqrt(1-(1+params[1])*params[0]**2*r**2))
        for i, term in enumerate(terms):
            result += params[i+2] * r ** term
        return result
    return sag_function

terms = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

params = [float(CV.EvaluateExpression(f"(cuy s{surface})")), float(CV.EvaluateExpression(f"(k s{surface})"))]
lower_bounds = [-80]
upper_bounds = [10]

for term in terms:
    if term == 2:
        sag_function = create_sag_function([])
        params, _ = curve_fit(sag_function, r, z, method='lm' , p0=params, maxfev=10000)
    else:
        params = np.append(params, 0)
        sag_function = create_sag_function(terms[1:len(params)-1])
        lower_bounds = [-80] * len(params)
        upper_bounds = [10] * len(params)
        params, _ = curve_fit(sag_function, r, z, bounds=(lower_bounds, upper_bounds), p0=params, maxfev=10000)

#params, _ = curve_fit(sag_function, r, z, method='lm' , p0=params, maxfev=10000)

fig = plt.figure(figsize=(18, 9), facecolor='white')

gs1 = fig.add_gridspec(nrows=1, ncols=1, left=0.02, right=0.25)
ax = fig.add_subplot(gs1[0,0])
ax.plot(sag_function(r,*params)-z, r)
ax.set_title('Sag_Error')

del _, lower_bounds, upper_bounds, terms, term, r, z

CV.Command("in cvuser:Juho_Macro\MY_MTF.seq");

file_path = 'C:\CVUSER\JUHOMTF.txt'

with open(file_path, 'r') as file:
    data = [[float(num) for num in line.strip().split()] for line in file]
    file.close()

x_data = data[0]
y_data = data[1:]

x_array = np.array(x_data)
y_arrays = np.array(y_data)

colors = ['#d62728', '#2ca02c', '#1f77b4', '#8c564b', '#e377c2']
line_styles = ['--', '-']

x_new = np.linspace(x_array.min(), x_array.max(), 300)

gs2 = fig.add_gridspec(nrows=1, ncols=2, left=0.28, right=0.99)
ax = fig.add_subplot(gs2[0,0])
ax.set_title('BEFORE MTF')

for index, y_array in enumerate(y_arrays,start = 1):
    field_num = index // 2
    line_style = line_styles[index % 2]
    f = interp1d(x_array, y_array, kind='cubic')
    y_new = f(x_new)
    ax.plot(x_new, y_new, linestyle=line_style, color=colors[field_num], label=f'Field {field_num + 1} {"Tangential" if index % 2 == 1 else "Radial"}')

params = params.tolist()
myasp = f"asp s{surface};rdy s{surface} {1/params[0]:.6f};k s{surface} {params[1]:.6f};A s{surface} {params[2]:.6e};B s{surface} {params[3]:.6e};C s{surface} {params[4]:.6e};D s{surface} {params[5]:.6e};E s{surface} {params[6]:.6e};F s{surface} {params[7]:.6e};G s{surface} {params[8]:.6e};H s{surface} {params[9]:.6e};J s{surface} {params[10]:.6e};set vig"

bfl = float(CV.EvaluateExpression("(thi si-1)"))
CV.Command(myasp)
defocus = float(CV.EvaluateExpression("(thi si-1)"))
defocus = bfl-defocus
mystr = f"thi si {defocus}"
CV.Command(mystr)

CV.Command("in cvuser:Juho_Macro\MY_MTF.seq");

file_path = 'C:\CVUSER\JUHOMTF.txt'

with open(file_path, 'r') as file:
    data = [[float(num) for num in line.strip().split()] for line in file]
    file.close()

x_data = data[0]
y_data = data[1:]

x_array = np.array(x_data)
y_arrays = np.array(y_data)

x_new = np.linspace(x_array.min(), x_array.max(), 300)

ax = fig.add_subplot(gs2[0,1])
ax.set_title('AFTER MTF')

for index, y_array in enumerate(y_arrays,start = 1):
    field_num = index // 2
    line_style = line_styles[index % 2]
    f = interp1d(x_array, y_array, kind='cubic')
    y_new = f(x_new)
    ax.plot(x_new, y_new, linestyle=line_style, color=colors[field_num], label=f'Field {field_num + 1} {"Tangential" if index % 2 == 1 else "Radial"}')

fig.savefig("C:\CVUSER\\MTF.png")

CV.StopCodeV()
print("success")
