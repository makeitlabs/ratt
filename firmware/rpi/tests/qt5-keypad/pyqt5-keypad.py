import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QFrame
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QSoundEffect
from PyQt5.QtCore import Qt, QUrl

class SoftKey(QLabel):
    def __init__(self, num, parent):
        assert num >= 0 and num <= 3
       
        labels = [ '\u21ba', '\u25bc', '\u25b2', '\u23ce' ]        
        xpositions = [ 0, 40, 80, 120 ]
        sfxfiles = [ 'sfx014.wav', 'sfx013.wav', 'sfx033.wav', 'sfx061.wav' ]
        label = labels[num]
        xpos = xpositions[num]
        sfx = sfxfiles[num]
        
        super().__init__(label, parent)

        self.sfx = QSoundEffect(self)
        self.sfx.setSource(QUrl.fromLocalFile(sfx));
        self.sfx.setVolume(0.5);
        
        self.resize(40,27);
        self.move(xpos, 100)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.showPressed(False)
        self.show()

    def showPressed(self, pressed):
        if pressed:
            self.sfx.play();
            self.setLineWidth(4)
        else:
            self.setLineWidth(2)

class App(QWidget):

    def keyPressEvent(self, event):
        print('key press: {}'.format(event.key()))

        key = event.key();

        if (key == Qt.Key_Escape):
            self.labelEsc.showPressed(True)
        elif (key == Qt.Key_Down):
            self.labelDown.showPressed(True)
        elif (key == Qt.Key_Up):
            self.labelUp.showPressed(True)
        elif (key == Qt.Key_Return):
            self.labelEnter.showPressed(True)
        
    def keyReleaseEvent(self, event):
        print('key release: {}'.format(event.key()))

        key = event.key();

        if (key == Qt.Key_Escape):
            self.labelEsc.showPressed(False)
        elif (key == Qt.Key_Down):
            self.labelDown.showPressed(False)
        elif (key == Qt.Key_Up):
            self.labelUp.showPressed(False)
        elif (key == Qt.Key_Return):
            self.labelEnter.showPressed(False)

    def __init__(self):
        super().__init__()

        self.labelEsc = SoftKey(0, self)
        self.labelDown = SoftKey(1, self)
        self.labelUp = SoftKey(2, self)
        self.labelEnter = SoftKey(3, self)
        
        self.left = 0
        self.top = 0
        self.width = 160
        self.height = 128
        self.initUI()
        
    def initUI(self):
        
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.show()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
