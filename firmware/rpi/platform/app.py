import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt
from networker import NetWorker

class App(QWidget):

    def keyPressEvent(self, event):
        key = event.key();
        print('key press: {}'.format(key))
        if key == Qt.Key_Return:
            self.netWorker.setAuth(user='api', password='s33krit')
            self.netWorker.req(url='https://192.168.0.24:8443/auth/api/v1/resources/frontdoor/acl')
        
    def keyReleaseEvent(self, event):
        key = event.key();
        print('key release: {}'.format(key))

    def __init__(self):
        super().__init__()

        self.netWorker = NetWorker()
        
        self.initUI()
        
    def initUI(self):
        self.setGeometry(0, 0, 160, 128)
        self.show()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
