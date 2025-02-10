import win32gui
import win32con
import win32api
import win32ui
import time
from PIL import Image
import easyocr
import pyautogui
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

ZENGYISHILIAN_RECT = (0.8, 0.85, 0.95, 0.95)
ZENGYISHILIAN_EXIAN_RECT = (0.75, 0.25, 0.9, 0.35)
KAISHIZUOZHAN_RECT = (0.8, 0.85, 1, 1)
ZUOZHANZHONG_RECT = (0, 0, 0.2, 0.2)
XUANZEZENGYI_RECT = (0.4, 0, 0.6, 0.2)
ZENGYI_LEFT_RECT = (0, 0.2, 0.33, 0.4)
ZENGYI_MIDDLE_RECT = (0.33, 0.2, 0.66, 0.4)
ZENGYI_RIGHT_RECT = (0.66, 0.2, 1, 0.4)
DIUQI_RECT = (0, 0.8, 0.3, 1)
DIUQIQUEREN_RECT = (0.65, 0.65, 0.85, 0.75)
QUEREN_RECT = (0.4, 0.8, 0.6, 1)
TUICHU_RECT = (0.4, 0.8, 0.6, 1)

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
            return bbox
    return None

def click(hwnd, x, y):
    win32gui.SetForegroundWindow(hwnd)
    win32api.SetCursorPos((x, y))
    time.sleep(0.1)
    pyautogui.click(duration=0.1)

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
    log(f"已{'静音' if mute else '取消静音'} 尘白禁区")

reader = easyocr.Reader(['ch_sim'])
hwnd = get_window_handle('尘白禁区')
mute = True
mute_game_window("Game.exe", mute)
last_detect_time = time.time()
need_move_forward = True
while True:
    # 将按键检测放在最前面，以便及时响应
    if win32api.GetAsyncKeyState(win32con.VK_CONTROL) and win32api.GetAsyncKeyState(win32con.VK_F1):
        log("检测到 Esc，退出程序")
        break
    if win32api.GetAsyncKeyState(win32con.VK_CONTROL) and win32api.GetAsyncKeyState(win32con.VK_F2):
        mute = not mute
        mute_game_window("Game.exe", mute)
        # 防止连续按键
        time.sleep(0.5)
    now = time.time()
    if now - last_detect_time < 0.5:
        time.sleep(0.001)
        continue
    last_detect_time = now
    if not (is_window_available(hwnd) and win32gui.IsWindowVisible(hwnd)):
        log("未找到窗口，退出程序")
        break
    rect = get_window_rect(hwnd)
    img = capture_frame(rect)
    # 作战中
    text = ocr_image(img, reader, ZUOZHANZHONG_RECT)
    # bbox = find_text_with_confidence(text, '第')
    if "击败" in str(text):
        # 点击E键
        pyautogui.press('e')
        if need_move_forward:
            # 往前跑大约1秒
            pyautogui.keyDown('w')
            time.sleep(2.5)
            pyautogui.keyUp('w')
            need_move_forward = False
        log("检测到 作战中，释放常规技")
        continue
    # 选择增益
    text = ocr_image(img, reader, XUANZEZENGYI_RECT)
    bbox = find_text_with_confidence(text, '选择增益')
    if bbox:
        text = ocr_image(img, reader, ZENGYI_LEFT_RECT)
        bbox = find_text_with_confidence(text, '单体')
        if not bbox:
            x, y = get_real_click_position_nobbox(rect, ZENGYI_LEFT_RECT, img.size)
            click(hwnd, x, y)
        else:
            x, y = get_real_click_position(rect, ZENGYI_LEFT_RECT, img.size, bbox)
            click(hwnd, x, y)
        # 点击确定
        time.sleep(0.5)
        text = ocr_image(img, reader, QUEREN_RECT)
        bbox = find_text_with_confidence(text, '确认')
        if bbox:
            x, y = get_real_click_position(rect, QUEREN_RECT, img.size, bbox)
            click(hwnd, x, y)
            log("检测到 确认")
    # 点击丢弃
    text = ocr_image(img, reader, DIUQI_RECT)
    bbox = find_text_with_confidence(text, '丢弃')
    if bbox:
        x, y = get_real_click_position(rect, DIUQI_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 丢弃")
        continue
    # 点击丢弃确认
    text = ocr_image(img, reader, DIUQIQUEREN_RECT)
    bbox = find_text_with_confidence(text, '确定')
    if bbox:
        x, y = get_real_click_position(rect, DIUQIQUEREN_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 丢弃确定")
        continue
    # 增益试炼入口
    text = ocr_image(img, reader, ZENGYISHILIAN_RECT)
    bbox = find_text_with_confidence(text, '增益试炼')
    if bbox:
        x, y = get_real_click_position(rect, ZENGYISHILIAN_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 增益试炼")
        continue
    # 增益试炼：厄险
    text = ocr_image(img, reader, ZENGYISHILIAN_EXIAN_RECT)
    bbox = find_text_with_confidence(text, '厄险', 0.5)                                 # 在4k主屏2k副屏的设备下，若游戏窗口为720p且在副屏，识别率会降低，故将置信度门槛降低
    if bbox:
        x, y = get_real_click_position(rect, ZENGYISHILIAN_EXIAN_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 增益试炼：厄险")
        time.sleep(1)                                                                   # 有几率出现连点进入到队员上阵界面导致挂机失败，增加这里的延迟
        continue
    # 开始作战
    text = ocr_image(img, reader, KAISHIZUOZHAN_RECT)
    bbox = find_text_with_confidence(text, '开始作战')
    if bbox:
        x, y = get_real_click_position(rect, KAISHIZUOZHAN_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 开始作战")
        need_move_forward = True
        continue
    # 退出
    text = ocr_image(img, reader, TUICHU_RECT)
    bbox = find_text_with_confidence(text, '退出')
    if bbox:
        x, y = get_real_click_position(rect, TUICHU_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 退出")
mute_game_window("Game.exe", False)
