import os, sys

# Get the absolute path of the current script file

script_path = os.path.abspath(__file__)

# Get the root directory by going up one level from the script directory
project_root = os.path.dirname(os.path.dirname(script_path))

sys.path.insert(0, project_root)
sys.path.insert(0, os.getcwd())  # Add the current directory as well

from PyQt5.QtWidgets import QMainWindow, QPushButton, QApplication, QTextBrowser, QVBoxLayout, QWidget, QLabel, \
    QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QCoreApplication, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QFont

from apiWidget import ApiWidget
from script import get_recorded_text, check_microphone_access

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)  # HighDPI support

QApplication.setFont(QFont('Arial', 12))


class Thread(QThread):
    afterFinished = pyqtSignal(str)

    def __init__(self):
        super(Thread, self).__init__()

    def run(self):
        try:
            self.afterFinished.emit(get_recorded_text())
        except Exception as e:
            QMessageBox.critical(None, 'Error', f'Error: {e}')


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.__initVal()
        self.__initUi()

    def __initVal(self):
        self.__settings_ini = QSettings('settings.ini', QSettings.IniFormat)

        if not self.__settings_ini.contains('API_KEY'):
            self.__settings_ini.setValue('API_KEY', '')

        self.__api_key = self.__settings_ini.value('API_KEY', type=str)

        self.__wrapper = None

    def __initUi(self):
        self.setWindowTitle('PyQt microphone access and record example')

        apiWidget = ApiWidget(self.__api_key)
        apiWidget.apiKeyAccepted.connect(self.__api_key_accepted)

        self.__recordBtn = QPushButton('Record')
        self.__recordBtn.setCheckable(True)
        self.__recordBtn.toggled.connect(self.__run)

        self.__isMicAvailableLbl = QLabel('Microphone is available')

        self.__isMicAvailableBtn = QPushButton('Check microphone access')
        self.__isMicAvailableBtn.clicked.connect(self.__checkMicAccess)
        self.__isMicAvailableBtn.click()

        lay = QHBoxLayout()
        lay.addWidget(self.__isMicAvailableBtn)
        lay.addWidget(self.__isMicAvailableLbl)
        micAvailableWidget = QWidget()
        micAvailableWidget.setLayout(lay)

        self.__resultBrowser = QTextBrowser()

        lay = QVBoxLayout()
        lay.addWidget(apiWidget)
        lay.addWidget(micAvailableWidget)
        lay.addWidget(self.__recordBtn)
        lay.addWidget(self.__resultBrowser)

        mainWidget = QWidget()
        mainWidget.setLayout(lay)

        self.setCentralWidget(mainWidget)

    def __run(self, f):
        self.__t = Thread()
        self.__t.afterFinished.connect(self.__afterFinished)
        self.__t.started.connect(self.__started)
        self.__t.finished.connect(self.__finished)
        self.__t.start()

    def __checkMicAccess(self):
        f = check_microphone_access()
        if f:
            self.__isMicAvailableLbl.setText('Microphone is available')
        else:
            self.__isMicAvailableLbl.setText('Microphone is not available')
        self.__recordBtn.setEnabled(f)

    def __api_key_accepted(self, api_key):
        self.__API_KEY = api_key
        self.__settings_ini.setValue('API_KEY', api_key)
        self.__wrapper.set_api(api_key)

    def __started(self):
        print('started')

    def __afterFinished(self, text):
        self.__resultBrowser.setText(text)

    def __finished(self):
        print('finished')
        self.__recordBtn.setChecked(False)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())