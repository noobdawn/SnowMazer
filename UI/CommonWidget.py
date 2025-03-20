from qfluentwidgets import (CardWidget, setTheme, Theme, IconWidget, BodyLabel, CaptionLabel, PushButton,
                            TransparentToolButton, FluentIcon, RoundMenu, Action, ElevatedCardWidget,
                            ImageLabel, isDarkTheme, FlowLayout, MSFluentTitleBar, SimpleCardWidget,
                            HeaderCardWidget, InfoBarIcon, HyperlinkLabel, HorizontalFlipView,
                            PrimaryPushButton, TitleLabel, PillPushButton, setFont, ScrollArea,
                            VerticalSeparator, MSFluentWindow, NavigationItemPosition, GroupHeaderCardWidget,
                            ComboBox, SearchLineEdit, SubtitleLabel, TableWidget)
from qfluentwidgets import FluentIcon as FIF
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGraphicsOpacityEffect, QFrame
from PyQt5.QtGui import QIcon, QFont, QColor, QPainter
from PyQt5.QtCore import Qt, QPoint, QSize, QUrl, QRect, QPropertyAnimation
from qfluentwidgets.common.config import qconfig, Theme
from qfluentwidgets.components.widgets.acrylic_label import AcrylicBrush

from Utils.AutoUtils import LogWidget

def isDarkTheme():
    """ whether the theme is dark mode """
    return qconfig.theme == Theme.DARK

def theme():
    """ get theme mode """
    return qconfig.theme


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


class PictureBox(QWidget):
    """ 点击图片后，显示大图 """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        if isDarkTheme():
            tintColor = QColor(32, 32, 32, 200)
        else:
            tintColor = QColor(255, 255, 255, 160)

        self.acrylicBrush = AcrylicBrush(self, 30, tintColor, QColor(0, 0, 0, 0))

        self.opacityEffect = QGraphicsOpacityEffect(self)
        self.opacityAni = QPropertyAnimation(self.opacityEffect, b"opacity", self)
        self.opacityEffect.setOpacity(1)
        self.setGraphicsEffect(self.opacityEffect)

        self.vBoxLayout = QVBoxLayout(self)
        self.closeButton = TransparentToolButton(FluentIcon.CLOSE, self)
        self.flipView = HorizontalFlipView(self)
        self.nameLabel = BodyLabel('Image', self)
        self.pageNumButton = PillPushButton('1 / 4', self)

        self.pageNumButton.setCheckable(False)
        self.pageNumButton.setFixedSize(80, 32)
        setFont(self.nameLabel, 16, QFont.DemiBold)

        self.closeButton.setFixedSize(32, 32)
        self.closeButton.setIconSize(QSize(14, 14))
        self.closeButton.clicked.connect(self.fadeOut)

        self.vBoxLayout.setContentsMargins(26, 28, 26, 28)
        self.vBoxLayout.addWidget(self.closeButton, 0, Qt.AlignRight | Qt.AlignTop)
        self.vBoxLayout.addWidget(self.flipView, 1)
        self.vBoxLayout.addWidget(self.nameLabel, 0, Qt.AlignHCenter)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.pageNumButton, 0, Qt.AlignHCenter)
        
        self.flipView.currentIndexChanged.connect(self.setCurrentIndex)

        self.__ImagePathList = []


    def setCurrentIndex(self, index: int):
        self.nameLabel.setText(self.__ImagePathList[index].split('/')[-1])
        self.pageNumButton.setText(f'{index + 1} / {len(self.__ImagePathList)}')
        self.flipView.setCurrentIndex(index)


    def showPictureBox(self, index: int, imageList: list):
        self.__ImagePathList = imageList
        self.flipView.clear()
        self.flipView.addImages(imageList)
        imagePath = imageList[index]
        self.nameLabel.setText(imagePath.split('/')[-1])
        self.pageNumButton.setText(f'{index + 1} / {len(imageList)}')
        self.flipView.setCurrentIndex(index)
        self.fadeIn()


    def paintEvent(self, e):
        if self.acrylicBrush.isAvailable():
            return self.acrylicBrush.paint()

        painter = QPainter(self)
        painter.setPen(Qt.NoPen)
        if isDarkTheme():
            painter.setBrush(QColor(32, 32, 32))
        else:
            painter.setBrush(QColor(255, 255, 255))

        painter.drawRect(self.rect())


    def resizeEvent(self, e):
        w = self.width() - 52
        self.flipView.setItemSize(QSize(w, w * 9 // 16))

    def fadeIn(self):
        rect = QRect(self.mapToGlobal(QPoint()), self.size())
        self.acrylicBrush.grabImage(rect)

        self.opacityAni.setStartValue(0)
        self.opacityAni.setEndValue(1)
        self.opacityAni.setDuration(150)
        self.opacityAni.start()
        self.show()

    def fadeOut(self):
        self.opacityAni.setStartValue(1)
        self.opacityAni.setEndValue(0)
        self.opacityAni.setDuration(150)
        self.opacityAni.finished.connect(self._onAniFinished)
        self.opacityAni.start()

    def _onAniFinished(self):
        self.opacityAni.finished.disconnect()
        self.hide()