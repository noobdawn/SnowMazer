import win32gui
import win32con
import win32api
import cv2
import dxcam
from ctypes import windll, wintypes
import ctypes
import numpy as np

# 获取显示器信息
monitor_info = None
def get_monitor_info(hwnd):
    global monitor_info
    if monitor_info is not None:
        return monitor_info    
    monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
    monitor_info = win32api.GetMonitorInfo(monitor)
    return monitor_info


def get_monitor_index(hwnd):
    """
    根据窗口句柄获取其所在的显示器索引（0-based）
    """    
    # 枚举所有显示器，获取它们的句柄列表
    monitors = win32api.EnumDisplayMonitors()

    # 排序，根据显示器的左上角坐标
    monitors.sort(key=lambda x: x[2][0])

    # 获取窗口左上角坐标
    x, y = get_monitor_position(hwnd)

    # 查找窗口所在的显示器
    for i, monitor in enumerate(monitors):
        monitor_rect = monitor[2]
        if monitor_rect[0] <= x < monitor_rect[2] and monitor_rect[1] <= y < monitor_rect[3]:
            return i    
    
    return 0  # 默认返回第一个显示器
    

# 获取显示器尺寸
def get_monitor_size(hwnd):
    monitor_info = get_monitor_info(hwnd)
    monitor_rect = monitor_info['Monitor']
    width = monitor_rect[2] - monitor_rect[0]
    height = monitor_rect[3] - monitor_rect[1]
    return width, height


# 获取显示器左上角坐标
def get_monitor_position(hwnd):
    monitor_info = get_monitor_info(hwnd)
    monitor_rect = monitor_info['Monitor']
    x, y = monitor_rect[0], monitor_rect[1]
    return x, y


# 判断窗口样式
def get_window_style(hwnd):
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    
    # 判断是否有边框和标题栏
    has_caption = (style & win32con.WS_CAPTION) == win32con.WS_CAPTION
    has_thickframe = (style & win32con.WS_THICKFRAME) == win32con.WS_THICKFRAME
    
    if has_caption or has_thickframe:
        return "窗口化"
    else:
        return "无边框"


# 设置窗口位置
def set_window_to_left_top(hwnd):
    x, y = get_monitor_position(hwnd)
    window_rect = win32gui.GetWindowRect(hwnd)
    window_width, window_height = window_rect[2] - window_rect[0], window_rect[3] - window_rect[1]

    # 设置窗口位置
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        x,
        y,
        window_width,
        window_height,
        win32con.SWP_SHOWWINDOW
    )
    print("窗口已移动到左上角")
    
    return True


# 截取图像
def crop_image_with_pixel(image, rect):
    left, top, right, bottom = rect
    return image[top:bottom, left:right]


def crop_image_with_scale(image, rect):
    width, height = image.shape[1], image.shape[0]
    left, top, right, bottom = rect
    left, top, right, bottom = int(left * width), int(top * height), int(right * width), int(bottom * height)
    return image[top:bottom, left:right]


class ScreenCapturer:
    def __init__(self, hwnd):
        self.hwnd = hwnd

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

        print("缩放比例:", windll.shcore.GetScaleFactorForDevice(0) / 100)
        print(windll.shcore.GetScaleFactorForDevice(1))

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

    
    def stop(self):
        self.camera.stop()


    def get_latest_frame(self):
        '''获取最新帧(RGB)'''
        frame = self.camera.get_latest_frame()
        if frame is None:
            return None
        return frame


def map_process(image):
    '''对小地图进行处理，使其更加清晰'''
    # 过滤出灰色区域，这里是墙壁
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    lower_gray = np.array([80, 80, 80], dtype=np.uint8)
    upper_gray = np.array([120, 120, 120], dtype=np.uint8)
    wall_mask = cv2.inRange(image, lower_gray, upper_gray)
    # 2. 形态学处理（去除噪点+细化线条）
    kernel = np.ones((3,3), np.uint8)
    cleaned = cv2.morphologyEx(wall_mask, cv2.MORPH_OPEN, kernel)  # 去噪
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    final_mask = np.zeros_like(cleaned)
    for cnt in contours:
        if cv2.contourArea(cnt) > 5:
            cv2.drawContours(final_mask, [cnt], -1, 255, -1)

    return wall_mask


# 主函数
def main():
    hwnd = win32gui.FindWindow(None, "驱入虚空")    
    if not hwnd:
        print("未找到指定窗口")
        return    
    print("找到目标窗口句柄:", hwnd)
    
    # 获取窗口样式
    style = get_window_style(hwnd)
    print("当前窗口模式:", style)
    
    # 设置窗口位置
    if style == "窗口化":
        set_window_to_left_top(hwnd)

    # 开始捕获屏幕
    capturer = ScreenCapturer(hwnd)
    capturer.start()

    while True:
        frame = capturer.get_latest_frame()
        if frame is  None:
            continue
        
        # 地图位于左上角的256x256区域
        map_scale_rect = (0.0, 0.0, 256.0 / 1600, 256.0 / 900)
        map_image = crop_image_with_scale(frame, map_scale_rect)
        cv2.imwrite("map.png", map_image)

        map_image = map_process(map_image)

        cv2.imshow("map", map_image)
        # 将窗口放到目标窗口的右边
       #  cv2.moveWindow("map", capturer.width, 0)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capturer.stop()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    # 请求管理员权限（可能需要）
    try:
        main()
    except Exception as e:
        print("操作失败:", e)
        input("按回车退出...")