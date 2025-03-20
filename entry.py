from UI.MainWindow import MainWindow
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import os
import ctypes
# 获取系统 DPI 缩放比例（Windows 示例）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    scale_factor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
except:
    scale_factor = 1.0

# 在创建 QApplication 实例前设置环境变量和属性
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR"] = str(scale_factor)
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"

# 启用高 DPI 缩放
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)  # 确保图片清晰

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())