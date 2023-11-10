import pandas as pd
import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QComboBox,
    QCheckBox,
    QMessageBox
)

def reblock_model(config):
    block_model = config['df']
    # set original coordinates to block origin
    block_model[config['X']] -= config['dx'] / 2
    block_model[config['Y']] -= config['dy'] / 2
    block_model[config['Z']] -= config['dz'] / 2

    # calculate the block coordinates in the new grid
    block_model['rx'] = (block_model[config['X']] // config['rdx']) * config['rdx']
    block_model['ry'] = (block_model[config['Y']] // config['rdy']) * config['rdy']
    block_model['rz'] = (block_model[config['Z']] // config['rdz']) * config['rdz']

    # set reblocked coordinates to block centroid
    block_model['rx'] += config['rdx'] / 2
    block_model['ry'] += config['rdy'] / 2
    block_model['rz'] += config['rdz'] / 2

    # Group by the reblocked coordinates and calculate reblocked values for each block in each column
    reblocked_model = block_model.groupby(['rx', 'ry', 'rz']).agg({
        **{column: 'sum'
           for column in config['sum']},
        **{column: 'mean'
           for column in config['mean']},
        **{column: lambda x: (x * block_model.loc[x.index, config['pounder']]).sum() / block_model.loc[x.index, config['pounder']].sum()
           for column in config['p_mean']},
    }).reset_index()
    # rename reblocked coordinates
    reblocked_model.rename(columns={'rx': 'X', 'ry': 'Y', 'rz': 'Z'}, inplace=True)
    reblocked_model.to_csv(config['output'], index=False)

class Tela1(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('File Selection')
        layout = QVBoxLayout()
        label = QLabel('Select the CSV model file:')
        layout.addWidget(label)

        file_select_button = QPushButton('Selecionar Arquivo CSV')
        file_select_button.clicked.connect(self.abrir_dialogo_arquivo)
        layout.addWidget(file_select_button)

        self.arquivo_selecionado = None

        self.setLayout(layout)

        self.config = {
            'df': None
        }

    def abrir_dialogo_arquivo(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter('CSV (*.csv)')

        if file_dialog.exec():
            arquivo_selecionado = file_dialog.selectedFiles()
            if arquivo_selecionado:
                self.arquivo_selecionado = arquivo_selecionado[0]
                try:
                    self.config['df'] = pd.read_csv(self.arquivo_selecionado)
                    self.abrir_tela2()
                except pd.errors.EmptyDataError:
                    print('The file is empty.')
                except pd.errors.ParserError:
                    print('The file could not be parsed.')

    def abrir_tela2(self):
        self.tela2 = Tela2(self.config)
        self.tela2.show()
        self.hide()

class Tela2(QWidget):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle('Coordinates Selection')
        self.config = config

        layout = QVBoxLayout()
        label = QLabel('Select the coordinates columns (X, Y, Z):')
        layout.addWidget(label)

        self.comboboxes = {
            'X': QComboBox(),
            'Y': QComboBox(),
            'Z': QComboBox()
        }

        for coluna in config['df'].columns:
            for key in self.comboboxes.keys():
                self.comboboxes[key].addItem(coluna)

        layout.addWidget(self.comboboxes['X'])
        layout.addWidget(self.comboboxes['Y'])
        layout.addWidget(self.comboboxes['Z'])

        label_dimensoes = QLabel('Inform the model dimensions (dx, dy, dz):')
        layout.addWidget(label_dimensoes)

        self.dx_input = QLineEdit()
        self.dy_input = QLineEdit()
        self.dz_input = QLineEdit()

        layout.addWidget(self.dx_input)
        layout.addWidget(self.dy_input)
        layout.addWidget(self.dz_input)

        label_dimensoes_reblocado = QLabel('Inform the reblocked dimensions (rdx, rdy, rdz):')
        layout.addWidget(label_dimensoes_reblocado)

        self.rdx_input = QLineEdit()
        self.rdy_input = QLineEdit()
        self.rdz_input = QLineEdit()

        layout.addWidget(self.rdx_input)
        layout.addWidget(self.rdy_input)
        layout.addWidget(self.rdz_input)

        confirm_button = QPushButton('Confirm')
        confirm_button.clicked.connect(self.obter_colunas_e_dimensoes)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

    def obter_colunas_e_dimensoes(self):
        self.config['X'] = self.comboboxes['X'].currentText()
        self.config['Y'] = self.comboboxes['Y'].currentText()
        self.config['Z'] = self.comboboxes['Z'].currentText()

        self.config['dx'] = float(self.dx_input.text())
        self.config['dy'] = float(self.dy_input.text())
        self.config['dz'] = float(self.dz_input.text())

        self.config['rdx'] = float(self.rdx_input.text())
        self.config['rdy'] = float(self.rdy_input.text())
        self.config['rdz'] = float(self.rdz_input.text())

        self.abrir_tela3()

    def abrir_tela3(self):
        self.tela3 = Tela3(self.config)
        self.tela3.show()
        self.hide()

class Tela3(QWidget):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle('Sum Selection')
        self.config = config

        layout = QVBoxLayout()
        label = QLabel('Select the columns to sum:')
        layout.addWidget(label)

        self.checkboxes = {}
        for coluna in self.config['df'].columns:
            if coluna not in [self.config['X'], self.config['Y'], self.config['Z']]:
                checkbox = QCheckBox(coluna)
                layout.addWidget(checkbox)
                self.checkboxes[coluna] = checkbox

        confirm_button = QPushButton('Confirm')
        confirm_button.clicked.connect(self.salvar_colunas_selecionadas)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

    def salvar_colunas_selecionadas(self):
        self.config['sum'] = [coluna for coluna, checkbox in self.checkboxes.items() if checkbox.isChecked()]
        self.abrir_tela4()

    def abrir_tela4(self):
        self.tela4 = Tela4(self.config)
        self.tela4.show()
        self.hide()

class Tela4(QWidget):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle('Mean Selection')
        self.config = config

        layout = QVBoxLayout()
        label = QLabel('Select the columns to mean:')
        layout.addWidget(label)

        self.checkboxes = {}
        for coluna in self.config['df'].columns:
            if coluna not in [self.config['X'], self.config['Y'], self.config['Z']]:
                if coluna not in self.config['sum']:
                    checkbox = QCheckBox(coluna)
                    layout.addWidget(checkbox)
                    self.checkboxes[coluna] = checkbox

        confirm_button = QPushButton('Confirm')
        confirm_button.clicked.connect(self.salvar_colunas_selecionadas)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

    def salvar_colunas_selecionadas(self):
        self.config['mean'] = [coluna for coluna, checkbox in self.checkboxes.items() if checkbox.isChecked()]
        self.abrir_tela5()

    def abrir_tela5(self):
        self.tela5 = Tela5(self.config)
        self.tela5.show()
        self.hide()

class Tela5(QWidget):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle('Weighted Mean Selection')
        self.config = config

        layout = QVBoxLayout()

        label = QLabel('Select the weighter column:')
        layout.addWidget(label)

        self.combobox = QComboBox()

        for coluna in config['df'].columns:
            self.combobox.addItem(coluna)

        layout.addWidget(self.combobox)

        label = QLabel('Select the columns to weighted mean:')
        layout.addWidget(label)

        self.checkboxes = {}
        for coluna in self.config['df'].columns:
            if coluna not in [self.config['X'], self.config['Y'], self.config['Z']]:
                if coluna not in self.config['sum']:
                    if coluna not in self.config['mean']:
                        checkbox = QCheckBox(coluna)
                        layout.addWidget(checkbox)
                        self.checkboxes[coluna] = checkbox

        confirm_button = QPushButton('Confirm')
        confirm_button.clicked.connect(self.salvar_colunas_selecionadas)
        layout.addWidget(confirm_button)

        self.setLayout(layout)

    def salvar_colunas_selecionadas(self):
        self.config['pounder'] = self.combobox.currentText()
        self.config['p_mean'] = [coluna for coluna, checkbox in self.checkboxes.items() if checkbox.isChecked()]
        self.abrir_tela6()

    def abrir_tela6(self):
        self.tela6 = Tela6(self.config)
        self.tela6.show()
        self.hide()

class Tela6(QWidget):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle('Output Selection')
        self.config = config

        layout = QVBoxLayout()
        label_local = QLabel('Inform the output file:')
        layout.addWidget(label_local)

        self.local_arquivo_input = QLineEdit()
        layout.addWidget(self.local_arquivo_input)

        confirmar_button = QPushButton('Confirm')
        confirmar_button.clicked.connect(self.gerar_resultado)
        layout.addWidget(confirmar_button)

        self.setLayout(layout)

    def gerar_resultado(self):
        self.config['output'] = self.local_arquivo_input.text()
        reblock_model(self.config)
        # Chame sua função de reblocagem e salve o resultado no arquivo especificado
        QMessageBox.information(self, 'Warning', 'Reblocking completed.', QMessageBox.Ok)
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    tela1 = Tela1()
    tela1.show()
    sys.exit(app.exec())
