from PyQt5 import QtCore, QtGui, QtWidgets
from qfluentwidgets import (CardWidget, setTheme, Theme, IconWidget, BodyLabel, CaptionLabel, PushButton,
                            TransparentToolButton, FluentIcon, RoundMenu, Action, ElevatedCardWidget,
                            ImageLabel, isDarkTheme, FlowLayout, MSFluentTitleBar, SimpleCardWidget,
                            HeaderCardWidget, InfoBarIcon, HyperlinkLabel, HorizontalFlipView,
                            PrimaryPushButton, TitleLabel, PillPushButton, setFont, ScrollArea,
                            VerticalSeparator, MSFluentWindow, NavigationItemPosition, GroupHeaderCardWidget,
                            ComboBox, SearchLineEdit, ProgressRing, IndeterminateProgressBar, CheckBox, SwitchButton, InfoBar)
from UI.CommonWidget import InterfaceWithLog, PictureBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout, QStackedWidget, QStackedLayout, QFrame, QSpacerItem, QSizePolicy
from Utils.IntoTheVoidUtils import *


class SquareAutoCombatCard(SimpleCardWidget):
    def __init__(self, pictureBox : PictureBox, parent=None):
        super().__init__(parent)
        self.setObjectName("SquareAutoCombatCard")

        self.pictureBox = pictureBox
        self._ImageList = [
            "Image\\IntoTheVoid\\烽燧广场虫妹配置.jpg",
            "Image\\IntoTheVoid\\烽燧广场挂机位置.jpg",
        ]

        self.nameLabel = TitleLabel("自动战斗：烽燧广场")
        self.combatButton = PrimaryPushButton("开始战斗")
        self.descriptionLabel = BodyLabel("烽燧广场挂机配置：虫妹，堆减耗和持续时间。\n"
                                          + "挂机方法：进入副本后，直接点击开始战斗即可。\n"
                                          + "注意事项：不要一次性打过多轮次，以免召唤物无法应付足够强度的敌人。\n"
                                          + "推荐二号位携带首领光环，如果是机枪哥更好。")
        self.progressBar = IndeterminateProgressBar()
        self.progressBar.stop()

        self.useSecondCharacter = CheckBox("使用第二角色以获得更多经验")
        self.useSecondCharacter.setChecked(True)
        self.wavelabel = CaptionLabel("每次战斗轮次：")
        self.waveSelect = ComboBox()
        for i in range(1, 16):
            self.waveSelect.addItem(str(i))
        self.waveSelect.setCurrentIndex(0)
        self.configSeparator = VerticalSeparator()
        self.qIntervalLabel = CaptionLabel("Q技能释放间隔：")
        self.qIntervalEdit = SearchLineEdit()
        self.qIntervalEdit.setPlaceholderText("单位：秒")
        self.qIntervalEdit.setFixedWidth(100)
        self.configSeparator1 = VerticalSeparator()

        # 展示截图
        self.flipView = HorizontalFlipView(self)
        self.flipView.addImages(self._ImageList)

        self.flipView.clicked.connect(lambda index: self.pictureBox.showPictureBox(self.pictureBox.flipView.currentIndex(), self._ImageList))
        self.combatButton.clicked.connect(self.onCombatButtonClicked)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.switchLayout = QHBoxLayout()
        self.configLayout = QHBoxLayout()

        self.initLayout()
        self.setBorderRadius(8)


    def initLayout(self):        
        self.vBoxLayout.addWidget(self.progressBar)

        self.hBoxLayout.setSpacing(30)
        self.hBoxLayout.setContentsMargins(34, 24, 24, 24)
        # icon
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(10)

        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addWidget(self.combatButton, 0, QtCore.Qt.AlignRight)


        # config
        self.vBoxLayout.addSpacing(10)
        self.configLayout.setContentsMargins(0, 0, 0, 0)
        self.configLayout.setSpacing(10)
        self.configLayout.addWidget(self.wavelabel)
        self.configLayout.addWidget(self.waveSelect)
        self.configLayout.addWidget(self.configSeparator1)
        self.configLayout.addWidget(self.qIntervalLabel)
        self.configLayout.addWidget(self.qIntervalEdit)
        self.configLayout.addWidget(self.configSeparator)
        self.configLayout.addWidget(self.useSecondCharacter)
        self.configLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.vBoxLayout.addLayout(self.configLayout, 0)

        # description
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # flip view
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.flipView)


# region 仅在调试模式开启时，才能显示四方向距离
    def onDebugSwitch(self, checked):
        self.distanceSwitch.setEnabled(checked)
        self.distanceLabel.setEnabled(checked)
        if not checked:
            self.distanceSwitch.setChecked(False)
            self.onDistanceSwitch(False)

    def onDistanceSwitch(self, checked):
        pass
# endregion

    def onCombatButtonClicked(self):
        if isSquareWorking():
            stopSquareDefense()
            self.progressBar.stop()
            self.progressBar.hide()
            self.combatButton.setText("开始战斗")
            return
        if IsThreadWorking():
            InfoBar.errorr(
                title="失败",
                content="其他自动战斗正在进行中",
                orient=QtCore.Qt.Horizontal,
                isClosable=True,
                position = InfoBar.Position.TOP,
                duration = 3000,
                parent=self
            )
        wave = int(self.waveSelect.currentText())
        # 如果输入不合法，直接设置为10
        try:
            qInterval = float(self.qIntervalEdit.text())
        except:
            qInterval = 10
            self.qIntervalEdit.setText("10")
        needSwitch = self.useSecondCharacter.isChecked()
        startSquareDefense(wave, qInterval, needSwitch)
        self.progressBar.start()
        self.combatButton.setText("停止战斗")



class MonumentAutoCombatCard(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MonumentAutoCombatCard")



class WalledCityAutoCombatCard(SimpleCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WalledCityAutoCombatCard")

        
        self.debugSwitch = SwitchButton()
        self.debugLabel = CaptionLabel("调试模式")
        self.distanceSwitch = SwitchButton()
        self.distanceLabel = CaptionLabel("显示四方向距离")
        self.switchSeparator = VerticalSeparator()

        # 仅在调试模式开启时，才能显示四方向距离
        self.debugSwitch.checkedChanged.connect(lambda checked: self.onDebugSwitch(checked))
        self.distanceSwitch.checkedChanged.connect(lambda checked: self.onDistanceSwitch(checked))
        

    def initLayout(self):
        
        # switch
        self.vBoxLayout.addSpacing(10)
        self.switchLayout.setContentsMargins(0, 0, 0, 0)
        self.switchLayout.setSpacing(20)
        self.switchLayout.addWidget(self.debugLabel, 0)
        self.switchLayout.addWidget(self.debugSwitch, 0)
        self.switchLayout.addWidget(self.switchSeparator, 0)
        self.switchLayout.addWidget(self.distanceLabel, 0)
        self.switchLayout.addWidget(self.distanceSwitch, 0)
        self.switchLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.vBoxLayout.addLayout(self.switchLayout, 0)



class Ui_IntoTheVoidInterface(InterfaceWithLog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("IntoTheVoidInterface")
        self.pictureBox = PictureBox(self)
        self.pictureBox.hide()

        self.SquareAutoCombatCard = SquareAutoCombatCard(self.pictureBox, parent=self.view)
        self.MonumentAutoCombatCard = MonumentAutoCombatCard(self.view)
        self.WalledCityAutoCombatCard = WalledCityAutoCombatCard(self.view)

        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.addWidget(self.SquareAutoCombatCard, 0, QtCore.Qt.AlignTop)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.addWidget(self.MonumentAutoCombatCard, 0, QtCore.Qt.AlignTop)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.addWidget(self.WalledCityAutoCombatCard, 0, QtCore.Qt.AlignTop)

        self.enableTransparentBackground()
        

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.pictureBox.resize(self.size())