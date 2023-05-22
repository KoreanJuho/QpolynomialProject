import sys
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow
from PyQt5.QtGui import QPixmap
import win32com.client
import numpy as np
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

form_window = uic.loadUiType("C:\\Fitting\\First.ui")[0]

class WindowClass(QMainWindow, form_window):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        #Start Code V
        self.CV = win32com.client.Dispatch('CODEV.Command.202203_SR1')
        self.CV.SetStartingDirectory("C:\CVUSER")
        self.CV.StartCodeV()
        
        #Ui
        self.Openfile.clicked.connect(self.Openfiles)
        self.Quit.clicked.connect(self.Quits)
        self.Fitting.clicked.connect(self.Fittings)
        self.SagError.clicked.connect(self.Sag_Errors)
        self.BeforeMTF.clicked.connect(self.Before_MTFs)
        self.AfterMTF.clicked.connect(self.After_MTFs)
        self.Savefile.clicked.connect(self.Savefiles)
    
    def Openfiles(self):
        fname = QFileDialog.getOpenFileName(self, "Open file", "C:\\CVUSER", "Sequence files (*.seq)")
        self.filepath.setText(fname[0])
        mypth = f"run {fname[0]};GO"
        self.CV.Command(mypth)
    
    def Savefiles(self):
        fname = QFileDialog.getSaveFileName(self, "Save file", "C:\\CVUSER", "Sequence files (*.seq)")
        self.filepath.setText(fname[0])
        mypth = f"WRL {fname[0]}"
        self.CV.Command(mypth)
    
    def Quits(self):
        self.CV.StopCodeV()
        QApplication.instance().quit()
        
    def Getrsag(self, surface_number):
        mysur = f"in C:CVUSER\\Juho_Macro\\rsag.seq {surface_number}"
        self.CV.Command(mysur)
    
        file_path = 'C:\\CVUSER\\sag.txt'

        with open(file_path, 'r') as file:
            lines = file.readlines()
            data = [list(map(float, line.strip().split())) for line in lines[1:]]
            file.close()

        r = np.array([row[0] for row in data])
        z = np.array([row[1] for row in data])
        
        return  r, z
    
    def Fits(self, surface_number, r, z):
        def create_sag_function(terms):
            def sag_function(r, *params):
                result = params[0]*r**2/(1+np.sqrt(1-(1+params[1])*params[0]**2*r**2))
                for i, term in enumerate(terms):
                    result += params[i+2] * r ** term
                return result
            return sag_function

        terms = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

        cuy = float(self.CV.EvaluateExpression(f"(cuy s{surface_number})"))
        k = float(self.CV.EvaluateExpression(f"(k s{surface_number})"))
        params = [cuy, k]
        
        lower_bounds = [-80, -80]
        upper_bounds = [2, 2]

        for weight, term in enumerate(terms):
            if term == 2:
                sag_function = create_sag_function([])
                params, _ = curve_fit(sag_function, r[0:300], z[0:300], bounds=(lower_bounds, upper_bounds) , p0=params, maxfev=10000)
            else:
                params = np.append(params, 0)
                sag_function = create_sag_function(terms[1:len(params)-1])
                lower_bounds = [-80] * len(params)
                upper_bounds = [10] * len(params)
                slice_index = 1600 + weight*100
                params, _ = curve_fit(sag_function, r[0:slice_index], z[0:slice_index], bounds=(lower_bounds, upper_bounds), p0=params, maxfev=10000)#bounds=(lower_bounds, upper_bounds)

        plt.clf()
        plt.plot(sag_function(r,*params)-z, r)
        plt.title("Sag Error")
        plt.savefig("C:\\Fitting\\Sag_Error.png", dpi=300, bbox_inches='tight')
        
        return params.tolist()
    
    def DrawMTF(self, freq):
        plt.clf()
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
            plt.plot(x_new, y_new, linestyle=line_style, color=colors[field_num % 5], label=f'Field {field_num + 1} {"Tangential" if index % 2 == 1 else "Radial"}')
    
    def EnterASP(self, surface, params):
        bfl = float(self.CV.EvaluateExpression("(thi si-1)"))
        myasp = f"asp s{surface};rdy s{surface} {1/params[0]:.6f};k s{surface} {params[1]:.6f};A s{surface} {params[2]:.6e};B s{surface} {params[3]:.6e};C s{surface} {params[4]:.6e};D s{surface} {params[5]:.6e};E s{surface} {params[6]:.6e};F s{surface} {params[7]:.6e};G s{surface} {params[8]:.6e};H s{surface} {params[9]:.6e};J s{surface} {params[10]:.6e};set vig"
        self.CV.Command(myasp)
        defocus = float(self.CV.EvaluateExpression("(thi si-1)"))
        defocus = bfl-defocus
        mystr = f"thi si {defocus}"
        self.CV.Command(mystr)
        
    def Fittings(self):
        surface_num = int(self.SurfaceNum.text())
        spatial_freq = int(self.SpatialFreq.text())
        r , z = self.Getrsag(surface_num)
        params = self.Fits(surface_num, r, z)
        self.DrawMTF(spatial_freq)
        plt.title(f"Before MTF s{surface_num} {spatial_freq}lp/mm")
        plt.savefig("C:\\Fitting\\BeforeMTF.png", dpi=1000, bbox_inches='tight')
        self.EnterASP(surface_num, params)
        self.DrawMTF(spatial_freq)
        plt.title(f"After MTF s{surface_num} {spatial_freq}lp/mm")
        plt.savefig("C:\\Fitting\\AfterMTF.png", dpi=1000, bbox_inches='tight')
        self.finish.setText(f"finish s{surface_num}")
        
    def Sag_Errors(self):
        QPixmapVar = QPixmap()
        QPixmapVar.load("C:\\Fitting\\Sag_Error.png")
        scaled_pixmap = QPixmapVar.scaled(self.Graphic.width(), self.Graphic.height(), Qt.KeepAspectRatio)
        self.Graphic.setPixmap(scaled_pixmap)
        
    def Before_MTFs(self):
        QPixmapVar = QPixmap()
        QPixmapVar.load("C:\\Fitting\\BeforeMTF.png")
        scaled_pixmap = QPixmapVar.scaled(self.Graphic.width(), self.Graphic.height(), Qt.KeepAspectRatio)
        self.Graphic.setPixmap(scaled_pixmap)
        
    def After_MTFs(self):
        QPixmapVar = QPixmap()
        QPixmapVar.load("C:\\Fitting\\AfterMTF.png")
        scaled_pixmap = QPixmapVar.scaled(self.Graphic.width(), self.Graphic.height(), Qt.KeepAspectRatio)
        self.Graphic.setPixmap(scaled_pixmap)
    
    
app = QApplication(sys.argv)
mainWindow = WindowClass()
mainWindow.show()
app.exec_()