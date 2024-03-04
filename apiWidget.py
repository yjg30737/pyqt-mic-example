import requests

from qtpy.QtCore import QSettings, Signal
from qtpy.QtGui import QColor
from qtpy.QtWidgets import QPushButton, QWidget, QHBoxLayout, QLineEdit, QLabel


class ApiWidget(QWidget):
    apiKeyAccepted = Signal(str)

    def __init__(self, api_key: str = ''):
        super(QWidget, self).__init__()
        self.__initVal(api_key)
        self.__initUi()

    def __initVal(self, api_key: str):
        self.__api_key = api_key

    def __initUi(self):
        self.__apiLineEdit = QLineEdit()
        self.__apiLineEdit.setEchoMode(QLineEdit.Password)
        self.__apiLineEdit.setText(self.__api_key)

        submitBtn = QPushButton('Submit')
        submitBtn.clicked.connect(self.__setApi)

        self.__apiCheckPreviewLbl = QLabel()
        self.__apiCheckPreviewLbl.setVisible(False)

        lay = QHBoxLayout()
        lay.addWidget(QLabel('API KEY'))
        lay.addWidget(self.__apiLineEdit)
        lay.addWidget(submitBtn)
        lay.addWidget(self.__apiCheckPreviewLbl)

        self.setLayout(lay)

        if self.__api_key:
            self.__setApi()

    def __setApi(self):
        try:
            api_key = self.__apiLineEdit.text()
            response = requests.get('https://api.openai.com/v1/models', headers={'Authorization': f'Bearer {api_key}'})
            f = response.status_code == 200
            if f:
                self.__apiCheckPreviewLbl.setStyleSheet("color: {}".format(QColor(0, 200, 0).name()))
                self.__apiCheckPreviewLbl.setText('API key is valid')
                self.apiKeyAccepted.emit(api_key)
            else:
                raise Exception
        except Exception as e:
            self.__apiCheckPreviewLbl.setStyleSheet("color: {}".format(QColor(255, 0, 0).name()))
            self.__apiCheckPreviewLbl.setText('API key is invalid')
            print(e)
        finally:
            self.__apiCheckPreviewLbl.show()

    def getApi(self):
        return self.__apiLineEdit.text()