import win32gui
import win32con
import win32api
import win32ui
import time
from PIL import Image
import easyocr
import pyautogui
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

mouse_down = False
delta_time = 1.0 / 60


# 常见按键别名映射
key_aliases = {
    # 小键盘数字键
    'num0': win32con.VK_NUMPAD0,
    'num1': win32con.VK_NUMPAD1,
    'num2': win32con.VK_NUMPAD2,
    'num3': win32con.VK_NUMPAD3,
    'num4': win32con.VK_NUMPAD4,
    'num5': win32con.VK_NUMPAD5,
    'num6': win32con.VK_NUMPAD6,
    'num7': win32con.VK_NUMPAD7,
    'num8': win32con.VK_NUMPAD8,
    'num9': win32con.VK_NUMPAD9,
    # 兼容numpad前缀写法
    'numpad0': win32con.VK_NUMPAD0,
    'numpad1': win32con.VK_NUMPAD1,
    'numpad2': win32con.VK_NUMPAD2,
    'numpad3': win32con.VK_NUMPAD3,
    'numpad4': win32con.VK_NUMPAD4,
    'numpad5': win32con.VK_NUMPAD5,
    'numpad6': win32con.VK_NUMPAD6,
    'numpad7': win32con.VK_NUMPAD7,
    'numpad8': win32con.VK_NUMPAD8,
    'numpad9': win32con.VK_NUMPAD9,
    # 小键盘功能键
    'num_lock': win32con.VK_NUMLOCK,  # 数字锁定键
    'num_div': win32con.VK_DIVIDE,    # /
    'num_mul': win32con.VK_MULTIPLY,  # *
    'num_sub': win32con.VK_SUBTRACT,  # -
    'num_add': win32con.VK_ADD,       # +
    'num_dec': win32con.VK_DECIMAL,   # .
    'num_enter': win32con.VK_RETURN,  # 小键盘回车（需配合扩展键标志）
    # 别名兼容
    'numdel': win32con.VK_DECIMAL,    # 小键盘del（同.键）
    'numplus': win32con.VK_ADD,
    'numminus': win32con.VK_SUBTRACT,
    'nummul': win32con.VK_MULTIPLY,
    'numdiv': win32con.VK_DIVIDE,
    'space': win32con.VK_SPACE,
    'enter': win32con.VK_RETURN,
    'esc': win32con.VK_ESCAPE,
    'tab': win32con.VK_TAB,
    'backspace': win32con.VK_BACK,
    'shift': win32con.VK_SHIFT,
    'ctrl': win32con.VK_CONTROL,
    'alt': win32con.VK_MENU,
    'up': win32con.VK_UP,
    'down': win32con.VK_DOWN,
    'left': win32con.VK_LEFT,
    'right': win32con.VK_RIGHT,
}

def str_to_virtual_key(key_str):
    key_str = key_str.strip().lower()    
    
    # 检查别名
    if key_str in key_aliases:
        return key_aliases[key_str]
    
    # 处理单个字母（A-Z）
    if len(key_str) == 1 and key_str.isalpha():
        return ord(key_str.upper())
    
    # 处理主键盘数字（0-9）
    if key_str.isdigit():
        return ord('0') + int(key_str)
    
    # 尝试直接通过win32con常量获取（例如VK_F1）
    vk_name = f'VK_{key_str.upper()}'
    try:
        return getattr(win32con, vk_name)
    except AttributeError:
        raise ValueError(f"Unsupported key: {key_str}")

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}.{int(time.time() * 1000) % 1000:03d}] {msg}")

def get_window_handle(window_name):
    return win32gui.FindWindow(None, window_name)

def get_window_rect(hwnd):
    return win32gui.GetWindowRect(hwnd)

def is_window_available(hwnd):
    return hwnd != 0 and win32gui.IsWindow(hwnd)

def capture_frame(rect):
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top

    hwnd = win32gui.GetDesktopWindow()
    hwindc = win32gui.GetWindowDC(hwnd)
    srcdc = win32ui.CreateDCFromHandle(hwindc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(srcdc, width, height)
    memdc.SelectObject(bmp)
    memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)

    bmp_info = bmp.GetInfo()
    bmp_str = bmp.GetBitmapBits(True)

    img = Image.frombuffer(
        'RGB',
        (bmp_info['bmWidth'], bmp_info['bmHeight']),
        bmp_str, 'raw', 'BGRX', 0, 1
    )

    
    if img.size[1] > 1080:
        ratio = img.size[0] / img.size[1]
        img.resize((int(img.size[0] / ratio), 1080))

    img.save('temp.png')

    memdc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwindc)
    win32gui.DeleteObject(bmp.GetHandle())

    return img

def ocr_image(image, reader, rect_size = None):
    if rect_size is not None:
        width, height = image.size
        left = width * rect_size[0]
        top = height * rect_size[1]
        right = width * rect_size[2]
        bottom = height * rect_size[3]
    cropped_image = image.crop((left, top, right, bottom))
    cropped_image.save('temp_cropped.png')
    return reader.readtext('temp_cropped.png')

def find_text_with_confidence(ocr_results, target_text, min_confidence=0.8):
    for result in ocr_results:
        bbox, text, confidence = result
        if target_text in text and confidence > min_confidence:
            return bbox, text
    return None, None

def get_real_click_position(window_rect, ocr_rect_size, img_size, ocr_bbox):
    x = (ocr_bbox[0][0] + ocr_bbox[2][0]) // 2 + window_rect[0] + ocr_rect_size[0] * img_size[0]
    y = (ocr_bbox[0][1] + ocr_bbox[2][1]) // 2 + window_rect[1] + ocr_rect_size[1] * img_size[1]
    return int(x), int(y)

def get_real_click_position_nobbox(window_rect, ocr_rect_size, img_size):
    x = window_rect[0] + ocr_rect_size[0] * img_size[0] + img_size[0] * (ocr_rect_size[2] - ocr_rect_size[0]) // 2
    y = window_rect[1] + ocr_rect_size[1] * img_size[1] + img_size[1] * (ocr_rect_size[3] - ocr_rect_size[1]) // 2
    return int(x), int(y)

def mute_game_window(process_name, mute):
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
        if session.Process and session.Process.name() == process_name:
            volume.SetMute(mute, None)
    log(f"已{'静音' if mute else '取消静音'}")

def click(hwnd, x, y, use_pyautogui=True, is_right=False):
    # 使用实际点击和发送鼠标事件两种方式
    if use_pyautogui:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        win32api.SetCursorPos((x, y))
        time.sleep(delta_time)
        pyautogui.click(duration=delta_time, button='primary' if not is_right else 'secondary')
    else:
        # 发送鼠标移动事件
        win32api.SendMessage(hwnd, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x, y))
        time.sleep(delta_time)
        
        # 发送点击事件
        if is_right:
            win32api.SendMessage(hwnd, win32con.WM_RBUTTONDOWN, 0, win32api.MAKELONG(x, y))
            time.sleep(delta_time)
            win32api.SendMessage(hwnd, win32con.WM_RBUTTONUP, 0, win32api.MAKELONG(x, y))
        else:
            win32api.SendMessage(hwnd, win32con.WM_LBUTTONDOWN, 0, win32api.MAKELONG(x, y))
            time.sleep(delta_time)
            win32api.SendMessage(hwnd, win32con.WM_LBUTTONUP, 0, win32api.MAKELONG(x, y))

def key_down(hwnd, key, use_pyautogui=False, hold_time=delta_time):
    """发送按键按下事件
    
    Args:
        hwnd (int): 目标窗口句柄
        key (str/int): 按键名称或虚拟键码
        use_pyautogui (bool): 是否使用pyautogui模拟按键
        hold_time (float): 窗口激活后等待时间
    """
    if use_pyautogui:
        # 确保窗口在前台
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # 恢复窗口（如果最小化）
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(hold_time)
        pyautogui.keyDown(key)
    else:
        # 将字符串按键转换为虚拟键码
        if isinstance(key, str):
            virtual_key = str_to_virtual_key(key)
        else:
            virtual_key = key
        
        # 获取扫描码和扩展标志
        scan_code = win32api.MapVirtualKey(virtual_key, 0)
        is_extended = 0
        # 处理扩展键（如方向键、小键盘）
        if virtual_key in (
            win32con.VK_LEFT, win32con.VK_UP, win32con.VK_RIGHT, win32con.VK_DOWN,
            win32con.VK_INSERT, win32con.VK_DELETE, win32con.VK_HOME, win32con.VK_END,
            win32con.VK_NEXT, win32con.VK_PRIOR, win32con.VK_NUMLOCK,
            win32con.VK_DIVIDE, win32con.VK_MULTIPLY, win32con.VK_SUBTRACT,
            win32con.VK_ADD, win32con.VK_DECIMAL, win32con.VK_RETURN
        ):
            is_extended = 1
        
        # 构造lParam（参考Windows消息文档）
        # 位布局：重复次数（0-15）| 扫描码（16-23）| 扩展标志（24） | 保留（25-28） | 上下文状态（29） | 前一个状态（30） | 转换状态（31）
        repeat_count = 1
        lParam = (repeat_count & 0xFFFF) | (scan_code << 16) | (is_extended << 24)
        
        # 发送WM_KEYDOWN消息
        win32api.SendMessage(hwnd, win32con.WM_KEYDOWN, virtual_key, lParam)

def key_up(hwnd, key, use_pyautogui=False, hold_time=delta_time):
    """发送按键按下事件
    
    Args:
        hwnd (int): 目标窗口句柄
        key (str/int): 按键名称或虚拟键码
        use_pyautogui (bool): 是否使用pyautogui模拟按键
        hold_time (float): 窗口激活后等待时间
    """
    if use_pyautogui:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(hold_time)
        pyautogui.keyUp(key)
    else:
        if isinstance(key, str):
            virtual_key = str_to_virtual_key(key)
        else:
            virtual_key = key
        
        scan_code = win32api.MapVirtualKey(virtual_key, 0)
        is_extended = 0
        if virtual_key in (win32con.VK_LEFT, win32con.VK_UP, win32con.VK_RIGHT, win32con.VK_DOWN,
                          win32con.VK_INSERT, win32con.VK_DELETE, win32con.VK_HOME, win32con.VK_END,
                          win32con.VK_NEXT, win32con.VK_PRIOR, win32con.VK_NUMLOCK):
            is_extended = 1
        
        # 注意：转换状态位（31位）设置为1表示释放
        lParam = (1 & 0xFFFF) | (scan_code << 16) | (is_extended << 24) | (0x1 << 31)
        win32api.SendMessage(hwnd, win32con.WM_KEYUP, virtual_key, lParam)

def key_press(hwnd, key, use_pyautogui=False, press_duration=delta_time):
    """发送完整按键动作（按下+释放）"""
    key_down(hwnd, key, use_pyautogui)
    if not use_pyautogui:
        # 如果使用SendMessage，可能需要短暂延时
        time.sleep(press_duration)
    key_up(hwnd, key, use_pyautogui)