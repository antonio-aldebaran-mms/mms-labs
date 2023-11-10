from io import StringIO
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
    QMessageBox,
    QTextBrowser
)

# Function to perform operations between columns based on the user-provided expression
def perform_operations(col, expression, new_column_name):
    import numpy as np
    # Evaluate the expression using the eval function
    col[new_column_name] = eval(expression, locals())

# Function to fix the conditional expression
def fix_expression(expression):
    # Replace 'if(' with 'np.where('
    expression = expression.replace("if(", "np.where(")
    return expression

class InitialWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.df = pd.DataFrame()
        self.file = None

        self.setWindowTitle('File Selection')

        layout = QVBoxLayout()

        label = QLabel('Select the CSV model file:')
        layout.addWidget(label)

        file_select_button = QPushButton('Select File CSV')
        file_select_button.clicked.connect(self.abrir_dialogo_arquivo)
        layout.addWidget(file_select_button)

        self.setLayout(layout)

    def abrir_dialogo_arquivo(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter('CSV (*.csv)')

        if file_dialog.exec():
            arquivo_selecionado = file_dialog.selectedFiles()
            if arquivo_selecionado:
                try:
                    self.file = arquivo_selecionado[0]
                    self.df = pd.read_csv(self.file)
                    self.open_main_window()
                except pd.errors.EmptyDataError:
                    print('The file is empty.')
                except pd.errors.ParserError:
                    print('The file could not be parsed.')

    def open_main_window(self):
        self.main_window = MainWindow(self.file, self.df)
        self.main_window.show()
        self.hide()

class MainWindow(QWidget):
    def __init__(self, file, df):
        super().__init__()

        self.file = file
        self.df = df

        self.setWindowTitle('Main')

        layout = QVBoxLayout()

        add_button = QPushButton('Add Column')
        add_button.clicked.connect(self.show_add_window)
        layout.addWidget(add_button)

        rmv_button = QPushButton('Remove Column')
        rmv_button.clicked.connect(self.show_remove_window)
        layout.addWidget(rmv_button)

        info_button = QPushButton('Column Information')
        info_button.clicked.connect(self.show_info_window)
        layout.addWidget(info_button)

        save_button = QPushButton('Save Columns')
        save_button.clicked.connect(self.save_columns)
        layout.addWidget(save_button)

        self.setLayout(layout)

    def show_add_window(self):
        self.add_window = AddWindow(self, self.df)
        self.add_window.show()
        self.hide()

    def show_remove_window(self):
        self.remove_window = RemoveWindow(self, self.df)
        self.remove_window.show()
        self.hide()

    def show_info_window(self):
        self.info_window = InfoWindow(self, self.df)
        self.info_window.show()
        self.hide()

    def save_columns(self):
        self.df.to_csv(self.file, index=False)
        QMessageBox.information(self, 'Warning', 'Columns saved!', QMessageBox.Ok)

class AddWindow(QWidget):
    def __init__(self, mw, df):
        super().__init__()

        self.mw = mw
        self.df = df

        self.setWindowTitle('Add Column')

        layout = QVBoxLayout()

        columns_label = QLabel("Available columns:")
        layout.addWidget(columns_label)
        columns_text = QTextBrowser()
        columns_text.setPlainText('\n'.join(self.df.columns))
        layout.addWidget(columns_text)

        new_column_label = QLabel("New column name:")
        layout.addWidget(new_column_label)
        self.new_column = QLineEdit()
        self.new_column.setPlaceholderText("New Column")
        layout.addWidget(self.new_column)

        expression_label = QLabel("Expression:")
        layout.addWidget(expression_label)
        self.expression = QLineEdit()
        self.expression.setPlaceholderText("if(col['A'] > col['B'], col['A'], col['B'])")
        layout.addWidget(self.expression)

        run_button = QPushButton('OK')
        run_button.clicked.connect(self.add_column)
        layout.addWidget(run_button)

        run_button = QPushButton('Return')
        run_button.clicked.connect(self.back)
        layout.addWidget(run_button)

        self.setLayout(layout)

    def add_column(self):
        expression = fix_expression(self.expression.text())
        new_column = self.new_column.text()
        perform_operations(self.df, expression, new_column)
        QMessageBox.information(self, 'Warning', 'Column added!', QMessageBox.Ok)
        self.back()

    def back(self):
        self.hide()
        self.mw.show()

class RemoveWindow(QWidget):
    def __init__(self, mw, df):
        super().__init__()
        self.mw = mw
        self.df = df

        self.setWindowTitle('Remove Column')

        layout = QVBoxLayout()

        label = QLabel('Select the column to remove:')
        layout.addWidget(label)

        self.combobox = QComboBox()
        for coluna in self.df.columns:
            self.combobox.addItem(coluna)
        layout.addWidget(self.combobox)

        run_button = QPushButton('OK')
        run_button.clicked.connect(self.remove_column)
        layout.addWidget(run_button)

        run_button = QPushButton('Return')
        run_button.clicked.connect(self.back)
        layout.addWidget(run_button)

        self.setLayout(layout)

    def remove_column(self):
        column = self.combobox.currentText()
        self.df.drop(column, axis=1, inplace=True)
        QMessageBox.information(self, 'Warning', 'Column removed!', QMessageBox.Ok)
        self.back()

    def back(self):
        self.hide()
        self.mw.show()

class InfoWindow(QWidget):
    def __init__(self, mw, df):
        super().__init__()
        self.mw = mw
        self.df = df

        self.setWindowTitle('Show Column')

        layout = QVBoxLayout()

        label = QLabel('Select the column to show:')
        layout.addWidget(label)
        self.combobox = QComboBox()
        for coluna in self.df.columns:
            self.combobox.addItem(coluna)
        layout.addWidget(self.combobox)

        info_label = QLabel("Information:")
        layout.addWidget(info_label)
        self.info_text = QTextBrowser()
        layout.addWidget(self.info_text)

        run_button = QPushButton('OK')
        run_button.clicked.connect(self.print_information)
        layout.addWidget(run_button)

        run_button = QPushButton('Return')
        run_button.clicked.connect(self.back)
        layout.addWidget(run_button)

        self.setLayout(layout)

    def print_information(self):
        column_name = self.combobox.currentText()

        original_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Calculate statistics
            mean_value = self.df[column_name].mean()
            median_value = self.df[column_name].median()
            standard_deviation = self.df[column_name].std()
            minimum_value = self.df[column_name].min()
            maximum_value = self.df[column_name].max()
            quartiles = self.df[column_name].quantile([0.25, 0.5, 0.75])
            num_observations = self.df[column_name].count()
            most_frequent_value = self.df[column_name].mode().iloc[0]

            # Print the statistics
            print(f"Statistics for column '{column_name}':")
            print(f"Mean: {mean_value}")
            print(f"Median: {median_value}")
            print(f"Standard Deviation: {standard_deviation}")
            print(f"Minimum: {minimum_value}")
            print(f"Maximum: {maximum_value}")
            print(f"Quartiles: Q1 = {quartiles[0.25]}, Q2 (Median) = {quartiles[0.5]}, Q3 = {quartiles[0.75]}")
            print(f"Number of Observations: {num_observations}")
            print(f"Most Frequent Value (Mode): {most_frequent_value}")

            unique_values = sorted(self.df[column_name].unique())
            min_diff = float('inf')
            for i in range(1, len(unique_values)):
                diff = unique_values[i] - unique_values[i - 1]
                if diff < min_diff:
                    min_diff = diff
            print(f"Min difference: {min_diff}")

        finally:
            output_content = sys.stdout.getvalue()
            sys.stdout = original_stdout

        self.info_text.setPlainText(output_content)

    def back(self):
        self.hide()
        self.mw.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InitialWindow()
    window.show()
    sys.exit(app.exec())
