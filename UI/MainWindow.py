from qfluentwidgets import NavigationItemPosition, FluentWindow
from qfluentwidgets import FluentIcon as FIF
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from UI.CommonWidget import Widget, InterfaceWithLog
from UI.Ui_IntoTheVoidInterface import Ui_IntoTheVoidInterface



class MainWindow(FluentWindow):
    """ Main Interface """

    def __init__(self):
        super().__init__()

        # Create sub-interfaces, when actually using, replace Widget with your own sub-interface
        self.homeInterface = Widget('Home Interface', self)
        self.snowbreakInterface = InterfaceWithLog(self)
        self.intothevoidInterface = Ui_IntoTheVoidInterface(self)
        self.settingInterface = Widget('Setting Interface', self)
        self.albumInterface = Widget('Album Interface', self)
        self.albumInterface1 = Widget('Album Interface 1', self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, 'Home')
        self.addSubInterface(self.snowbreakInterface, "Icon/snowbreak.ico", 'Snowbreak')
        self.addSubInterface(self.intothevoidInterface, "Icon/intothevoid.ico", 'IntoTheVoid')

        self.navigationInterface.addSeparator()

        self.addSubInterface(self.albumInterface, FIF.ALBUM, 'Albums', NavigationItemPosition.SCROLL)
        self.addSubInterface(self.albumInterface1, FIF.ALBUM, 'Album 1', parent=self.albumInterface)

        self.addSubInterface(self.settingInterface, FIF.SETTING, 'Settings', NavigationItemPosition.BOTTOM)

    def initWindow(self):
        self.resize(900, 700)
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.setWindowTitle('PyQt-Fluent-Widgets')