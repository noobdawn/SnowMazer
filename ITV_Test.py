import win32gui
import win32con
import win32api
import cv2
import dxcam
from ctypes import windll, wintypes
import ctypes
import numpy as np
import math
from Utils.AutoUtils import *
from Utils.IntoTheVoidUtils import *

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


def detect_arrow_orientation(minimap_image):
    # 1. 转换为RGB并提取颜色掩膜
    rgb = cv2.cvtColor(minimap_image, cv2.COLOR_BGR2RGB)
    low_rgb = np.array([200, 150, 75])
    high_rgb = np.array([255, 200, 90])
    mask = cv2.inRange(rgb, low_rgb, high_rgb)
    
    # 2. 形态学去噪
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # 3. 轮廓检测与筛选
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    
    valid_contours = [cnt for cnt in contours if 100 < cv2.contourArea(cnt) ]
    if not valid_contours:
        return None
    
    arrow_contour = max(valid_contours, key=cv2.contourArea)
    
    # 4. 提取箭头主方向（使用PCA分析）
    # 将轮廓点转换为适合PCA的格式
    points = arrow_contour.reshape(-1, 2).astype(np.float32)
    
    # 执行PCA分析
    mean, eigenvectors = cv2.PCACompute(points, mean=None)
    
    # 获取主方向向量
    (vx, vy), (nx, ny) = eigenvectors  # 第一主成分是最大方差方向
    
    # 确定方向向量的正负（通过比较两端点距离质心的长度）
    center = mean[0]
    direction_vector = np.array([vx, vy])
    
    # 生成两个可能的端点
    pt1 = center + direction_vector * 20  # 正方向延伸
    pt2 = center - direction_vector * 20  # 负方向延伸
    
    # 找出实际指向端（距离轮廓点更远的一端）
    max_dist = 0
    far_pt = pt1
    for pt in [pt1, pt2]:
        dist = np.max([np.linalg.norm(p - pt) for p in points])
        if dist > max_dist:
            max_dist = dist
            far_pt = pt
    
    # 计算最终方向向量（从质心指向远端点）
    final_vector = far_pt - center
    
    # 5. 计算角度并转换到标准坐标系（0度指向正东，逆时针增加）
    angle = np.degrees(np.arctan2(-final_vector[1], final_vector[0]))  # y轴取反转换为标准坐标系
    angle = angle % 360  # 规范化到0-360度
    
    # 6. 二次验证（通过凸包检测尖端）
    hull = cv2.convexHull(arrow_contour, returnPoints=False)
    defects = cv2.convexityDefects(arrow_contour, hull)
    
    # 寻找最大的凸缺陷（对应箭头底部凹陷）
    if defects is not None:
        max_defect = max(defects, key=lambda x: x[0][3])
        start, end, far, depth = max_defect[0]
        
        # 根据凸缺陷位置微调角度
        tip_point = tuple(arrow_contour[start][0])
        opposite_vector = np.array(tip_point) - center
        tip_angle = np.degrees(np.arctan2(-opposite_vector[1], opposite_vector[0])) % 360
        
        # 如果两个角度差异较大，使用凸缺陷计算结果
        if abs(angle - tip_angle) > 30:
            angle = tip_angle

    return -angle + 180 - 45


def get_wall_mask(image):
    '''对小地图进行处理，使其更加清晰'''
    # 提取墙壁
    lower_gray = np.array([80, 80, 80], dtype=np.uint8)
    upper_gray = np.array([120, 120, 120], dtype=np.uint8)
    wall_mask = cv2.inRange(image, lower_gray, upper_gray)

    R = image[:, :, 2]  # 红色通道
    G = image[:, :, 1]  # 绿色通道
    B = image[:, :, 0]  # 蓝色通道
    g_condition = (G * 2 > R + B + 20)
    filter_mask = np.where(g_condition, 0, 255).astype(np.uint8) 
    wall_mask = cv2.bitwise_and(wall_mask, filter_mask)

    # 形态学处理
    wall_mask = cv2.erode(wall_mask, np.ones((2, 2), np.uint8), iterations=1)
    wall_mask = cv2.dilate(wall_mask, np.ones((2, 2), np.uint8), iterations=1)

    contours, _ = cv2.findContours(wall_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    valid_contours =  [cnt for cnt in contours if cv2.contourArea(cnt) > 20]

    final_mask = np.zeros_like(wall_mask)
    for cnt in valid_contours:
        if cv2.contourArea(cnt) > 5:
            cv2.drawContours(final_mask, [cnt], -1, 255, -1)

    return final_mask


def get_distance_from_direction(wall_mask, angle, near, far):
    '''
    从指定的方向获取距离
    :param wall_mask: 一张256x256的墙壁掩膜，二值图像，0表示可通行，255表示墙壁
    :param angle: 方向角度，90度指向正下方，0度指向正右方，-90度指向正上方
    :param near: 检测开始的最近距离
    :param far: 检测结束的最远距离
    '''
    wall_mask = np.asarray(wall_mask)
    center = (128.0, 128.0)  # 浮点型中心坐标
    angle_rad = math.radians(angle)
    
    # 计算方向单位向量（数学坐标系）
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)

    # 配置检测参数
    step = 0.5  # 平衡精度与性能的步长
    max_steps = int((far - near) / step) + 1

    for t in np.linspace(near, far, max_steps):
        # 计算当前检测点坐标
        x = center[0] + dx * t
        y = center[1] + dy * t
        
        # 坐标规范化
        xi, yi = int(round(x)), int(round(y))
        
        # 边界有效性检查
        if 0 <= xi < 256 and 0 <= yi < 256:
            if wall_mask[yi, xi] == 255:
                return t  # 命中返回
        else:
            # 射线完全越界时提前终止
            beyond_x = not (0 <= x < 256)
            beyond_y = not (0 <= y < 256)
            if beyond_x and beyond_y:
                break

    return 256  # 未命中返回


CONDITIONS_RIGHT_DISTANCE_BIGGER_THAN = 1
CONDITIONS_LEFT_DISTANCE_BIGGER_THAN = 2
CONDITIONS_UP_DISTANCE_BIGGER_THAN = 3
CONDITIONS_DOWN_DISTANCE_BIGGER_THAN = 4
CONDITIONS_RIGHT_DISTANCE_BELOW = 5
CONDITIONS_LEFT_DISTANCE_BELOW = 6
CONDITIONS_UP_DISTANCE_BELOW = 7
CONDITIONS_DOWN_DISTANCE_BELOW = 8

ACTION_KEY_DOWN = 1
ACTION_KEY_UP = 2
ACTION_KEY_PRESS = 3
ACTION_MOUSE_DOWN = 4
ACTION_MOUSE_UP = 5


class Action:
    def __init__(self, end_condition, distance, start_action, start_keycodes, end_action, end_keycodes):
        self.end_condition = end_condition
        self.condition_distance = distance
        self.start_action = start_action
        self.end_action = end_action
        self.start_keycode = start_keycodes
        self.end_keycode = end_keycodes


ACTION_QUEUE = []
CURRENT_ACTION = None

# 添加动作
# 直到右侧有足够距离前为止，向左前方移动
# ACTION_QUEUE.append(Action(CONDITIONS_RIGHT_DISTANCE_BIGGER_THAN, 50, ACTION_KEY_DOWN, ['a', 'w'], ACTION_KEY_UP, ['a', 'w']))
# # 直到右侧的距离不足30，向右前方移动
# ACTION_QUEUE.append(Action(CONDITIONS_RIGHT_DISTANCE_BELOW, 30, ACTION_KEY_DOWN, ['d', 'w'], ACTION_KEY_UP, ['d', 'w']))


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

    # 开始捕获屏幕
    capturer = ScreenCapturer(hwnd)
    capturer.start()

    while True:
        frame = capturer.get_latest_frame()
        if frame is  None:
            continue
        
        # 地图位于左上角的256x256区域
        map_rect = (0, 0, 256, 256)
        map_scale_rect = (0.0, 0.0, 256 / 1600, 256 / 900)
        map_image = crop_image_with_scale(frame, map_scale_rect)
        map_image = cv2.resize(map_image, (256, 256))

        wall_mask = get_wall_mask(map_image)
        angle = detect_arrow_orientation(map_image)

        right_distance = get_distance_from_direction(wall_mask, 0, 20, 256)
        left_distance = get_distance_from_direction(wall_mask, 180, 20, 256)
        up_distance = get_distance_from_direction(wall_mask, -90, 20, 256)
        down_distance = get_distance_from_direction(wall_mask, 90, 20, 256)


        def start_action(action):
            if action.start_action == ACTION_KEY_DOWN:
                for keycode in action.start_keycode:
                    key_down(hwnd, keycode)
            elif action.start_action == ACTION_KEY_UP:
                for keycode in action.start_keycode:
                    key_up(hwnd, keycode)
            elif action.start_action == ACTION_KEY_PRESS:
                for keycode in action.start_keycode:
                    key_press(hwnd, keycode)


        def end_action(action):
            if action.end_action == ACTION_KEY_DOWN:
                for keycode in action.end_keycode:
                    key_down(hwnd, keycode)
            elif action.end_action == ACTION_KEY_UP:
                for keycode in action.end_keycode:
                    key_up(hwnd, keycode)
            elif action.end_action == ACTION_KEY_PRESS:
                for keycode in action.end_keycode:
                    key_press(hwnd, keycode)
        

        def condition_check(action):
            if action.end_condition == CONDITIONS_RIGHT_DISTANCE_BIGGER_THAN:
                if right_distance > action.condition_distance:
                    return True
            elif action.end_condition == CONDITIONS_RIGHT_DISTANCE_BELOW:
                if right_distance < action.condition_distance:
                    return True
            elif action.end_condition == CONDITIONS_LEFT_DISTANCE_BIGGER_THAN:
                if left_distance > action.condition_distance:
                    return True
            elif action.end_condition == CONDITIONS_LEFT_DISTANCE_BELOW:
                if left_distance < action.condition_distance:
                    return True
            elif action.end_condition == CONDITIONS_UP_DISTANCE_BIGGER_THAN:
                if up_distance > action.condition_distance:
                    return True
            elif action.end_condition == CONDITIONS_UP_DISTANCE_BELOW:
                if up_distance < action.condition_distance:
                    return True
            elif action.end_condition == CONDITIONS_DOWN_DISTANCE_BIGGER_THAN:
                if down_distance > action.condition_distance:
                    return True
            elif action.end_condition == CONDITIONS_DOWN_DISTANCE_BELOW:
                if down_distance < action.condition_distance:
                    return True
            return False

        global CURRENT_ACTION, ACTION_QUEUE
        if CURRENT_ACTION is None:
            if len(ACTION_QUEUE) > 0:
                CURRENT_ACTION = ACTION_QUEUE.pop(0)
                start_action(CURRENT_ACTION)


        if CURRENT_ACTION is not None:
            if condition_check(CURRENT_ACTION):
                end_action(CURRENT_ACTION)
                CURRENT_ACTION = None


        # 绘制预览窗体
        preview_texture = cv2.cvtColor(wall_mask, cv2.COLOR_GRAY2BGR)
        if angle is not None:
            # 在地图上绘制一条射线
            center = (128, 128)
            length = 100
            radian = np.radians(angle)
            dx = int(length * np.cos(radian))
            dy = int(length * np.sin(radian))
            cv2.line(preview_texture, center, (center[0] + dx, center[1] + dy), (0, 255, 0), 2)
            cv2.putText(preview_texture, f"Angle: {angle:.2f} degree", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        else:
            cv2.putText(preview_texture, "No Arrow Found", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            
        cv2.putText(preview_texture, "r: " + str(right_distance), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(preview_texture, "l: " + str(left_distance), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(preview_texture, "u: " + str(up_distance), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(preview_texture, "d: " + str(down_distance), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        cv2.imshow("map", preview_texture)


        # 将窗口放到目标窗口的右边
        cv2.moveWindow("map", capturer.width, 0)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capturer.stop()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    # 请求管理员权限（可能需要）
    try:
        # time.sleep(5)
        main()
    except Exception as e:
        raise e