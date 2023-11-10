import sys
import ezdxf
import numpy as np
import csv
from scipy.spatial import cKDTree
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

def triangulate_surface(msp):
    triangles = []

    for entity in msp.query('3DFACE'):
        if isinstance(entity, ezdxf.entities.Face3d):
            # Extract the vertices
            vtx0 = np.array([entity.dxf.vtx0.x, entity.dxf.vtx0.y, entity.dxf.vtx0.z])
            vtx1 = np.array([entity.dxf.vtx1.x, entity.dxf.vtx1.y, entity.dxf.vtx1.z])
            vtx2 = np.array([entity.dxf.vtx2.x, entity.dxf.vtx2.y, entity.dxf.vtx2.z])

            # Triangulate the quadrilateral into two triangles
            triangles.append((vtx0, vtx1, vtx2))

    return np.vstack(triangles)

def load_csv_surface(csv_file):
    points = []

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            x, y, elevation = map(float, row)
            points.append((x, y, elevation))

    return np.array(points)

def project_surface_to_grid(dxf_surface, csv_surface):
    # Create a KD-tree for the DXF surface points for efficient nearest neighbor search
    dxf_tree = cKDTree(dxf_surface[:, :2])  # Consider only x and y coordinates for search

    projected_points = []

    for csv_point in csv_surface:
        # Find the nearest point on the DXF surface
        _, index = dxf_tree.query(csv_point[:2])

        # Update the coordinates of the CSV point with the elevation from the DXF surface
        dxf_elevation = dxf_surface[index][2]
        projected_point = np.array([csv_point[0], csv_point[1], dxf_elevation])
        projected_points.append(projected_point)

    return np.array(projected_points)

def save_csv(points, output_file):
    with open(output_file, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['X', 'Y', 'Z'])  # Header

        for x, y, z in points:
            writer.writerow([x, y, z])

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
                doc = ezdxf.readfile(arquivo_selecionado[0])
                msp = doc.modelspace()
                self.config['dxf'] = triangulate_surface(msp)

    def open_csv_dialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly

        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter('CSV (*.csv)')

        if file_dialog.exec():
            arquivo_selecionado = file_dialog.selectedFiles()
            if arquivo_selecionado:
                self.config['csv'] = load_csv_surface(arquivo_selecionado[0])

    def run_projection(self):
        projected_surface = project_surface_to_grid(self.config['dxf'], self.config['csv'])
        save_csv(projected_surface, self.output_local.text())
        QMessageBox.information(self, 'Warning', 'Projection completed.', QMessageBox.Ok)
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tela1 = Window()
    tela1.show()
    sys.exit(app.exec())
