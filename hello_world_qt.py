import sys
import random
sss

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        self.hello = ['hello world', '你好', 'こんにちは', '안녕하세요', 'hola']

        self.button = QtWidgets.QPushButton('Click me!')
        self.text = QtWidgets.QLabel('Hello World!', 
                                     alignment = QtCore.Qt.AlignCenter)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.magic)

    @QtCore.Slot()
    def magic(self):
        self.text.setText(random.choice(self.hello))

if __name__ == '__main__':
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(400, 300)
    widget.show()

    sys.exit(app.exec())