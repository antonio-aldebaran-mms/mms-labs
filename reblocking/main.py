import pandas as pd
import sys
from PySide6.QtGui import QFont, QIcon, QIntValidator
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
)

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

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Reblocking")
        self.setGeometry(100, 100, 400, 200)
        self.path_file = None
        int_validator = QIntValidator()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Form Layout
        layout = QVBoxLayout()
        font = QFont()
        font.setPixelSize(30)
        icon = QIcon("../labs/labs.ico")
        self.setWindowIcon(icon)

        label_original = QLabel("Original Dimensions:")
        label_original.setFont(font)
        layout.addWidget(label_original) 

        # Original Dimensions
        label_dx = QLabel("X:")
        self.input_dx = QLineEdit()
        self.input_dx.setValidator(int_validator)
        layout.addWidget(label_dx)
        layout.addWidget(self.input_dx)

        label_dy = QLabel("Y:")
        self.input_dy = QLineEdit()
        layout.addWidget(label_dy)
        layout.addWidget(self.input_dy)

        label_dz = QLabel("Z:")
        self.input_dz = QLineEdit()
        layout.addWidget(label_dz)
        layout.addWidget(self.input_dz)
        
        label_reblock = QLabel("Reblocked Dimensions:")
        label_reblock.setFont(font)
        layout.addWidget(label_reblock) 
        
        # Reblocked dimensions
        label_rdx = QLabel("X:")
        self.input_rdx = QLineEdit()
        layout.addWidget(label_rdx)
        layout.addWidget(self.input_rdx)

        label_rdy = QLabel("Y:")
        self.input_rdy = QLineEdit()
        layout.addWidget(label_rdy)
        layout.addWidget(self.input_rdy)

        label_rdz = QLabel("Z:")
        self.input_rdz = QLineEdit()
        layout.addWidget(label_rdz)
        layout.addWidget(self.input_rdz)   
        
        import_button = QPushButton("Select file")
        import_button.clicked.connect(self.open_file_dialog)
        layout.addWidget(import_button)

        self.submit_button = QPushButton("Ok")
        self.submit_button.clicked.connect(self.submit_form)
        self.submit_button.setEnabled(False)
        layout.addWidget(self.submit_button)

        central_widget.setLayout(layout)

    def submit_form(self):
        dx= self.input_dx.text()
        dy = self.input_dy.text()
        dz = self.input_dz.text()
        original_dimensions = [dx,dy,dz]
        
        rdx= self.input_rdx.text()
        rdy = self.input_rdy.text()
        rdz = self.input_rdz.text()
        reblock_dimensions = [rdx,rdy,rdz]     

        block_model = pd.read_csv(self.path_file)
        reblocked_model = reblock_model(block_model, original_dimensions, reblock_dimensions)
        reblocked_model.to_csv("results.csv", index=False)

    def open_file_dialog(self):
        options = QFileDialog.Options()
        self.path_file, _ = QFileDialog.getOpenFileName(self, "Select File", "", "CSV Files (*.csv);;All Files (*)", options=options)
        self.submit_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())
