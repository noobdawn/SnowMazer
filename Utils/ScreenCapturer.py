from Utils.AutoUtils import get_monitor_index
import win32gui
import win32con
from ctypes import windll
import dxcam


class ScreenCapturer:
    def __init__(self, hwnd):
        monitor_index = get_monitor_index(hwnd)

        self.camera = dxcam.create(
            device_idx=0,
            output_idx=monitor_index,
            output_color="BGR",
        )

        # 考虑到GetWindowRect获取的是窗口的外框，需要减去边框宽度
        # 先考虑标题栏
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        has_caption = (style & win32con.WS_CAPTION) == win32con.WS_CAPTION
        # 获得屏幕缩放比例
        self.scale_factor = windll.shcore.GetScaleFactorForDevice(0) / 100

        if has_caption:
            self.top = int(30 * self.scale_factor)
            self.left = int(8 * self.scale_factor)
        else:
            self.top = 0
            self.left = 0

        dx_rect = win32gui.GetClientRect(hwnd)
        self.width, self.height = dx_rect[2] - dx_rect[0], dx_rect[3] - dx_rect[1]


    def start(self):        
        self.camera.start(
            region=(self.left, self.top, self.width + self.left, self.height + self.top),
            target_fps=30,
        )
        self.camera.is_capturing = True

    
    def stop(self):
        self.camera.stop()
        self.camera.is_capturing = False


    def get_latest_frame(self):
        '''获取最新帧(RGB)'''
        frame = self.camera.get_latest_frame()
        if frame is None:
            return None
        return frame