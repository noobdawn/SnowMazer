import win32gui
import win32con
import win32api
import cv2
import dxcam

# 获取显示器信息
monitor_info = None
def get_monitor_info(hwnd):
    global monitor_info
    if monitor_info is not None:
        return monitor_info    
    monitor = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
    monitor_info = win32api.GetMonitorInfo(monitor)
    return monitor_info


# 获取显示器序号
def get_monitor_index(hwnd):
    monitor_info = get_monitor_info(hwnd)
    device_name = monitor_info['Device']
    monitor_index = int(device_name.split(":")[1])
    return monitor_index
    



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
    width, height = window_rect[2] - window_rect[0], window_rect[3] - window_rect[1]

    # 设置窗口位置
    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        x,
        y,
        width,
        height,
        win32con.SWP_SHOWWINDOW
    )
    print("窗口已移动到左上角")
    
    return True


class ScreenCapturer:
    def __init__(self, hwnd):
        self.hwnd = hwnd

        monitor_index = get_monitor_index(hwnd)

        self.camera = dxcam.create(
            device_idx=0,
            output_idx=monitor_index,
            output_color="RGB",
        )
        window_rect = win32gui.GetWindowRect(hwnd)
        self.left, self.top, self.right, self.bottom = window_rect
        self.width = self.right - self.left
        self.height = self.bottom - self.top
        self.camera.start(
            region=(0, 0, self.width, self.height),
            target_fps=30,
        )

    def start(self):
        try:
            while True:
                frame = self.camera.get_latest_frame()
                if frame is None:
                    continue
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite("screenshot.jpg", frame)
        finally:
            self.camera.stop()



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
    set_window_to_left_top(hwnd)

    capturer = ScreenCapturer(hwnd)
    capturer.start()


if __name__ == "__main__":
    # 请求管理员权限（可能需要）
    try:
        main()
    except Exception as e:
        print("操作失败:", e)
        input("按回车退出...")