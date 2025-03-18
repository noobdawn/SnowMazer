from qfluentwidgets import NavigationItemPosition, FluentWindow, SubtitleLabel, setFont, TableWidget, HeaderCardWidget, TransparentToolButton, FluentIcon
from qfluentwidgets import FluentIcon as FIF
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
import sys

from Utils.AutoUtils import LogWidget


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        # Must set a globally unique object name for the sub-interface
        self.setObjectName(text.replace(' ', '-'))


class LogTableWidget(QWidget, LogWidget):

    def __init__(self):
        super().__init__()
        
        self.hBoxLayout = QHBoxLayout(self)
        self.tableView = TableWidget(self)

        self.tableView.setBorderVisible(True)
        self.tableView.setBorderRadius(8)

        self.tableView.setWordWrap(False)
        self.tableView.setRowCount(0)
        self.tableView.setColumnCount(4)

        self.tableView.verticalHeader().hide()
        self.tableView.setHorizontalHeaderLabels(['时间', '等级', '内容', '标签'])
        self.tableView.resizeColumnsToContents()

        self.hBoxLayout.setSpacing(10)
        self.hBoxLayout.setContentsMargins(10, 30, 0, 0)
        self.hBoxLayout.addWidget(self.tableView)
        

    def addLog(self, time: str, level: str, content: str, tag: str):
        row = self.tableView.rowCount()
        self.tableView.setRowCount(row + 1)
        self.tableView.setItem(row, 0, QTableWidgetItem(time))
        self.tableView.setItem(row, 1, QTableWidgetItem(level))
        self.tableView.setItem(row, 2, QTableWidgetItem(content))
        self.tableView.setItem(row, 3, QTableWidgetItem(tag))

    def clearLog(self):
        self.tableView.setRowCount(0)


# 这是一个日志窗口，用于显示日志
# 一共四列，分别是时间、等级、内容、tag
# 用于显示日志
class LogCard(HeaderCardWidget, LogWidget):
    """ Log Card """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setTitle('日志')
        self.setBorderRadius(8)

        self.logTable = LogTableWidget()
        self.expandButton = TransparentToolButton(
            FluentIcon.CHEVRON_RIGHT_MED, self)
        
        self.expandButton.setFixedSize(32, 32)
        self.expandButton.setIconSize(QSize(12, 12))

        self.headerLayout.addWidget(self.expandButton, 0, Qt.AlignRight)
        self.viewLayout.addWidget(self.logTable)


# 在右侧部署一个日志窗口
class InterfaceWithLog(QFrame):
    
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)

        # Must set a globally unique object name for the sub-interface
        self.setObjectName(text.replace(' ', '-'))

        self.logCard = LogCard(self)
        self.hBoxLayout.addWidget(self.logCard, 1, Qt.AlignCenter)



class MainWindow(FluentWindow):
    """ Main Interface """

    def __init__(self):
        super().__init__()

        # Create sub-interfaces, when actually using, replace Widget with your own sub-interface
        self.homeInterface = Widget('Home Interface', self)
        self.snowbreakInterface = InterfaceWithLog('Snowbreak Interface', self)
        self.intothevoidInterface = Widget('IntoTheVoid Interface', self)
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