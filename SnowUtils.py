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

def search_hp_bar(image : Image.Image):
    # 找到整个画面中，R通道处于(200, 255)，G通道处于(75, 125)，B通道处于(75, 125)的所有像素
    img = image.convert('RGB')
    width, height = img.size
    pixels = img.load()
    hp_bar_pixels = []
    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            if 200 <= r <= 255 and 75 <= g <= 125 and 75 <= b <= 125:
                hp_bar_pixels.append((x, y))    
    if not hp_bar_pixels:
        return None, None
    # 计算中心位置
    sum_x = sum(pixel[0] for pixel in hp_bar_pixels)
    sum_y = sum(pixel[1] for pixel in hp_bar_pixels)
    center_x = sum_x // len(hp_bar_pixels)
    center_y = sum_y // len(hp_bar_pixels)    
    return center_x, center_y

    
def shoot(hwnd, aim_x, aim_y):
    win32gui.SetForegroundWindow(hwnd)
    win32api.SetCursorPos((aim_x, aim_y))
    # 按下鼠标左键
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)