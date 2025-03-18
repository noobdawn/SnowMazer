from qfluentwidgets import NavigationItemPosition, FluentWindow, SubtitleLabel, setFont, TableWidget, HeaderCardWidget, TransparentToolButton, FluentIcon, ScrollArea
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
        # 距离四周的距离
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
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


    @property
    def logger(self):
        return self.tableView


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


    def addLog(self, time: str, level: str, content: str, tag: str):
        self.logTable.addLog(time, level, content, tag)


    def clearLog(self):
        self.logTable.clearLog()


class InterfaceWithLog(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.view = QWidget(self)

        self.vBoxLayout = QVBoxLayout(self.view)
        self.logCard = LogCard(self.view)

        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setObjectName('InterfaceWithLog')

        self.vBoxLayout.setSpacing(10)
        # self.vBoxLayout.setContentsMargins(0, 0, 10, 30)
        self.vBoxLayout.addWidget(self.logCard, 0, Qt.AlignTop)

        self.enableTransparentBackground()
