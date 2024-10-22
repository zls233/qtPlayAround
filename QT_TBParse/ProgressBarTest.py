import sys
from PySide6 import QtWidgets as gui

class SampleBar(gui.QMainWindow):
    """Main Application"""


    def __init__(self, parent = None):
        print('Starting the main Application')
        super(SampleBar, self).__init__()
        self.initUI()

    def initUI(self):
        # Pre Params:
        self.setMinimumSize(800, 600)

        # File Menus & Status Bar:
        self.statusBar().showMessage('Ready')
        self.progressBar = gui.QProgressBar()


        self.statusBar().addPermanentWidget(self.progressBar)

        # This is simply to show the bar
        self.progressBar.setGeometry(30, 40, 200, 25)
        self.progressBar.setValue(50)

def main():
    app = gui.QApplication(sys.argv)
    main = SampleBar()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()