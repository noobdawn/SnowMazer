from PyQt5 import QtCore, QtGui, QtWidgets
from qfluentwidgets import SimpleCardWidget
from UI.CommonWidget import InterfaceWithLog


class SquareAutoCombatCard(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SquareAutoCombatCard")


class MonumentAutoCombatCard(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MonumentAutoCombatCard")



class WalledCityAutoCombatCard(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WalledCityAutoCombatCard")



class Ui_IntoTheVoidInterface(InterfaceWithLog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IntoTheVoidInterface")
        self.SquareAutoCombatCard = SquareAutoCombatCard(self)
        self.MonumentAutoCombatCard = MonumentAutoCombatCard(self)
        self.WalledCityAutoCombatCard = WalledCityAutoCombatCard(self)

        self.vBoxLayout.removeWidget(self.logCard)
        self.vBoxLayout.addWidget(self.SquareAutoCombatCard)
        self.vBoxLayout.addWidget(self.MonumentAutoCombatCard)
        self.vBoxLayout.addWidget(self.WalledCityAutoCombatCard)
        self.vBoxLayout.addWidget(self.logCard)
        