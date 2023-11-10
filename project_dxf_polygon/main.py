import sys
import csv
import ezdxf
import numpy as np
from shapely.geometry import Polygon, Point
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox
)

def read_dxf(filename):
    doc = ezdxf.readfile(filename)
    msp = doc.modelspace()
    polylines = [entity for entity in msp if entity.dxftype() == 'LWPOLYLINE']
    if not polylines:
        raise ValueError('No LWPOLYLINE found in DXF file.')
    # Assume there is only one LWPOLYLINE object in the DXF file
    polyline = polylines[0]
    polygon_points = [(vertex[0], vertex[1]) for vertex in polyline]
    # Make sure the polygon is closed
    if polygon_points[0] != polygon_points[-1]:
        polygon_points.append(polygon_points[0])
    return Polygon(polygon_points)


def read_csv(filename):
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        next(reader) # skip header
        data = [row for row in reader]
    return np.array(data, dtype=float)

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Project DXF Surface')

        layout = QVBoxLayout()

        dxf_label = QLabel('Select the DXF surface file:')
        layout.addWidget(dxf_label)
        dxf_select_button = QPushButton('Selecionar Arquivo DXF')
        dxf_select_button.clicked.connect(self.open_dxf_dialog)
        layout.addWidget(dxf_select_button)

        csv_label = QLabel('Select the CSV surface file:')
        layout.addWidget(csv_label)

        csv_select_button = QPushButton('Selecionar Arquivo CSV')
        csv_select_button.clicked.connect(self.open_csv_dialog)
        layout.addWidget(csv_select_button)

        elevation_label = QLabel('Inform the elevation:')
        layout.addWidget(elevation_label)
        self.elevation = QLineEdit()
        layout.addWidget(self.elevation)

        out_label = QLabel('Inform the output file:')
        layout.addWidget(out_label)
        self.output_local = QLineEdit()
        layout.addWidget(self.output_local)

        confirm_button = QPushButton('Confirm')
        confirm_button.clicked.connect(self.run_projection)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

        self.config = {
            'dxf': None,
            'csv': None
        }

    def open_dxf_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter('DXF (*.dxf)')

        if file_dialog.exec():
            arquivo_selecionado = file_dialog.selectedFiles()
            if arquivo_selecionado:
                self.config['dxf'] = read_dxf(arquivo_selecionado[0])

    def open_csv_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter('CSV (*.csv)')

        if file_dialog.exec():
            arquivo_selecionado = file_dialog.selectedFiles()
            if arquivo_selecionado:
                self.config['csv'] = read_csv(arquivo_selecionado[0])

    def run_projection(self):
         # Calculate surface points inside polygon
        surface_points = self.config['csv'][:, :2]
        mask = [self.config['dxf'].contains(Point(p)) for p in surface_points]
        elevations = np.zeros_like(self.config['csv'][:, 2])
        elevations[mask] = float(self.elevation.text())

        # Update surface data with elevations
        updated_data = self.config['csv'].copy()
        updated_data[:, 2] = np.where(mask, elevations, updated_data[:, 2])

        # Save output
        np.savetxt(self.output_local.text(), updated_data, delimiter=',', header='x,y,z', comments='')
        QMessageBox.information(self, 'Warning', 'Projection completed.', QMessageBox.Ok)
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tela1 = Window()
    tela1.show()
    sys.exit(app.exec())
