from PyQt5.QtWidgets import QDialog, QFileDialog
from .ui_dialog import Ui_Dialog  # Assuming ui_dialog.py is the converted .ui file

class YoloPredDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.rasterButton.clicked.connect(self.selectRasterFile)
        self.ui.outputDirButton.clicked.connect(self.selectOutputDir)

    def selectRasterFile(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Raster File", "", "Raster Files (*.tif *.tiff)")
        if file:
            self.ui.rasterLineEdit.setText(file)

    def selectOutputDir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if directory:
            self.ui.outputDirLineEdit.setText(directory)

    def getInputs(self):
        return self.ui.rasterLineEdit.text(), self.ui.outputDirLineEdit.text()