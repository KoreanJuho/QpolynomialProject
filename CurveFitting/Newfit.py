import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import numpy as np
import win32com.client
import tkinter as tk
from tkinter import filedialog, messagebox
import os

class ASP_fit:
    def __init__(self):
        #Start Code V
        self.CV = win32com.client.Dispatch('CODEV.Command.202203_SR1')
        self.CV.SetStartingDirectory("C:\CVUSER")
        self.CV.StartCodeV()

        #Make Graph (Sag Error, Before MTF, After MTF)
        self.fig = plt.figure(figsize=(18, 9), facecolor='white')

        gs = self.fig.add_gridspec(nrows=1, ncols=1, left=0.02, right=0.25)
        self.sag_error_graph = self.fig.add_subplot(gs[0, 0])
        self.sag_error_graph.set_title('Sag_Error')

        gs = self.fig.add_gridspec(nrows=1, ncols=2, left=0.28, right=0.99)
        self.Before_Mtf_graph = self.fig.add_subplot(gs[0, 0])
        self.Before_Mtf_graph.set_title('BEFORE MTF')
        self.After_Mtf_graph = self.fig.add_subplot(gs[0, 1])
        self.After_Mtf_graph.set_title('AFTER MTF')

    def OpenSeq(self):
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        
        file_path = None
        file_path = filedialog.askopenfilename(filetypes=[("Sequence files", "*.seq"), ("All files", "*.*")])
        
        while not file_path:
            messagebox.showwarning("No File Selected", "You must select a file to proceed.")
            file_path = filedialog.askopenfilename(filetypes=[("Sequence files", "*.seq"), ("All files", "*.*")])
        
        mypth = f"run {file_path};GO"
        self.CV.Command(mypth)

    def Getrsag(self, surface_number):
        # script_dir = os.path.dirname(os.path.realpath(__file__))
        # parent_dir = os.path.dirname(script_dir)
        # relative_path = os.path.join(parent_dir, "CodeV_Macro", "rsag.seq")
        # absolute_path = os.path.abspath(relative_path)
        
        # mysur = fr"in {absolute_path} {surface_number}"
        
        # self.CV.Command(mysur)
        
        # relative_path = os.path.join(parent_dir, "txtData", "sag.txt")
        # file_path = os.path.abspath(relative_path)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        file_path = r"../SAG.txt"
        
        with open(file_path, 'r') as file:
            lines = file.readlines()
            data = [list(map(float, line.strip().split())) for line in lines[1:]]
            file.close()

        r = np.array([row[0] for row in data])
        z = np.array([row[1] for row in data])
        
        return r, z
    
    def Fitting(self, r, z):
        # Create model
        def create_sag_function(terms):
            def sag_function(r, *params):
                result = 0
                for i, term in enumerate(terms):
                    result += params[i] * r ** term
                return result
            return sag_function

        terms = [4, 6, 8, 10, 12, 14, 16, 18, 20]

        params = []

        #This code is for mild surface
        for weight, term in enumerate(terms):
            params = np.append(params, 0)
            sag_function = create_sag_function(terms[0:len(params)])
            slice_index = 1600 + weight*100
            params, _ = curve_fit(sag_function, r[0:slice_index], z[0:slice_index], p0=params, maxfev=10000)

        #self.sag_error_graph.plot(sag_function(r,*params)-z, r)
        
        if term == 20:
            E = sum((z - sag_function(r, *params))**2)
            return params.tolist() , E
        
        return params.tolist()
    
    def DrawMTF(self, ax, freq):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        parent_dir = os.path.dirname(script_dir)
        relative_path = os.path.join(parent_dir, "CodeV_Macro", "MY_MTF.seq")
        absolute_path = os.path.abspath(relative_path)
        
        self.CV.Command(fr"in {absolute_path} {freq}")

        relative_path = os.path.join(parent_dir, "txtData", "JUHOMTF.txt")
        file_path = os.path.abspath(relative_path)

        with open(file_path, 'r') as file:
            data = [[float(num) for num in line.strip().split()] for line in file]
            file.close()

        x_data = data[0]
        y_data = data[1:]

        x_array = np.array(x_data)
        y_array = np.array(y_data)

        colors = ['#d62728', '#2ca02c', '#1f77b4', '#8c564b', '#e377c2']
        line_styles = ['--', '-']

        x_new = np.linspace(x_array.min(), x_array.max(), 300)

        for index, y_array in enumerate(y_array,start = 1):
            field_num = index // 2
            line_style = line_styles[index % 2]
            f = interp1d(x_array, y_array, kind='cubic')
            y_new = f(x_new)
            ax.plot(x_new, y_new, linestyle=line_style, color=colors[field_num % 5], label=f'Field {field_num + 1} {"Tangential" if index % 2 == 1 else "Radial"}')

    def EnterASP(self, surface, params):
        bfl = float(self.CV.EvaluateExpression("(thi si-1)"))
        myasp = f"asp s{surface};rdy s{surface} {1/params[0]:.6f};k s{surface} {params[1]:.6f};A s{surface} {params[2]:.6e};B s{surface} {params[3]:.6e};C s{surface} {params[4]:.6e};D s{surface} {params[5]:.6e};E s{surface} {params[6]:.6e};F s{surface} {params[7]:.6e};G s{surface} {params[8]:.6e};H s{surface} {params[9]:.6e};J s{surface} {params[10]:.6e};set vig"
        self.CV.Command(myasp)
        defocus = float(self.CV.EvaluateExpression("(thi si-1)"))
        defocus = bfl-defocus
        mystr = f"thi si {defocus}"
        self.CV.Command(mystr)
    
    def Savefig(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))
        parent_dir = os.path.dirname(script_dir)
        relative_path = os.path.join(parent_dir, "Graph", "MTF.png")
        absolute_path = os.path.abspath(relative_path)
        ft.fig.savefig(absolute_path)
    
    def StopCodeV(self):
        self.CV.StopCodeV()
        print("Turned Off")

ft = ASP_fit()
# ft.OpenSeq()

#ft.DrawMTF(ft.Before_Mtf_graph,150)

surface = 2
r , z = ft.Getrsag(surface)
params, E = ft.Fitting(r, z)
letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J']
asp_params = ''.join([f'{letters[i]} s{surface} {param:.6e}; ' for i, param in enumerate(params)])
myasp = f"asp s{surface};{asp_params}set vig"
print(myasp)
print(E)
# ft.EnterASP(surface_num, params)
# print(f"success {surface_num}")

#ft.DrawMTF(ft.After_Mtf_graph,150)
#ft.Savefig()

# mypth = "C:\CVUSER\\test_fit.seq"
# mypth = f"WRL {mypth}"
# ft.CV.Command(mypth)
# print("save")
# ft.StopCodeV()