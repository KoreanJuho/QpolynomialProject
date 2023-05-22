import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import numpy as np
import win32com.client
import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox

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

    def Getrsag(self,surface_number):
        # root = tk.Tk()
        # root.withdraw()  # Hide the root window
        # surface_number = simpledialog.askinteger("Surface Number", "Which surface want to fit?")
        mysur = f"in C:CVUSER\\Juho_Macro\\rsag.seq {surface_number}"
        self.CV.Command(mysur)
    
        file_path = 'C:\\CVUSER\\sag.txt'

        with open(file_path, 'r') as file:
            lines = file.readlines()
            data = [list(map(float, line.strip().split())) for line in lines[1:]]
            file.close()

        r = np.array([row[0] for row in data])
        z = np.array([row[1] for row in data])
        
        return r, z
    
    def Fitting(self, surface_number, r, z):
        def create_sag_function(terms):
            def sag_function(r, *params):
                result = params[0]*r**2/(1+np.sqrt(1-(1+params[1])*params[0]**2*r**2))
                for i, term in enumerate(terms):
                    result += params[i+2] * r ** term
                return result
            return sag_function

        #terms = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
        terms = [2, 20, 18, 16, 14, 12, 10, 8, 6, 4]

        cuy = float(self.CV.EvaluateExpression(f"(cuy s{surface_number})"))
        k = -1 #float(self.CV.EvaluateExpression(f"(k s{surface_number})"))
        params = [cuy, k]
        
        lower_bounds = [-80, -80]
        upper_bounds = [3, 3]

        for term in terms:
            if term == 2:
                sag_function = create_sag_function([])
                params, _ = curve_fit(sag_function, r[0:300], z[0:300], bounds=(lower_bounds, upper_bounds) , p0=params, maxfev=10000)
            else:
                params = np.append(params, 0)
                sag_function = create_sag_function(terms[1:len(params)-1])
                lower_bounds = [-80] * len(params)
                upper_bounds = [10] * len(params)
                #slice_index = 1600 + weight*100
                params, _ = curve_fit(sag_function, r, z, method='lm', p0=params, maxfev=10000)

        self.sag_error_graph.plot(sag_function(r,*params)-z, r)
        
        return params.tolist()
    
    def DrawMTF(self, ax, freq):
        self.CV.Command(f"in cvuser:Juho_Macro\MY_MTF.seq {freq}")

        file_path = 'C:\CVUSER\JUHOMTF.txt'

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
        myasp = f"asp s{surface};rdy s{surface} {1/params[0]:.6f};k s{surface} {params[1]:.6f};A s{surface} {params[10]:.6e};B s{surface} {params[9]:.6e};C s{surface} {params[8]:.6e};D s{surface} {params[7]:.6e};E s{surface} {params[6]:.6e};F s{surface} {params[5]:.6e};G s{surface} {params[4]:.6e};H s{surface} {params[3]:.6e};J s{surface} {params[2]:.6e};set vig"
        self.CV.Command(myasp)
        defocus = float(self.CV.EvaluateExpression("(thi si-1)"))
        defocus = bfl-defocus
        mystr = f"thi si {defocus}"
        self.CV.Command(mystr)
    
    def Savefig(self):
        ft.fig.savefig("C:\CVUSER\\MTF.png")
    
    def StopCodeV(self):
        self.CV.StopCodeV()
        print("Turned Off")
    
ft = ASP_fit()
ft.OpenSeq()

ft.DrawMTF(ft.Before_Mtf_graph,150)

# for surface_num in range(1,9):
surface_num = 2


r , z = ft.Getrsag(surface_num)
params = ft.Fitting(surface_num, r, z)
ft.EnterASP(surface_num, params)
print(f"success {surface_num}")

ft.DrawMTF(ft.After_Mtf_graph,150)
ft.Savefig()

mypth = "C:\CVUSER\\test_fit1.seq"
mypth = f"WRL {mypth}"
ft.CV.Command(mypth)
print("save")
ft.StopCodeV()