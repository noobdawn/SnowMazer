from SnowUtils import *

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
    if '击败' in str(text) or '目标' in str(text):
        # 点击E键
        pyautogui.press('e')
        if need_move_forward:
            # 往前跑大约1秒
            pyautogui.keyDown('w')
            time.sleep(2.5)
            pyautogui.keyUp('w')
            need_move_forward = False
        log("检测到 作战中，释放常规技")
        time.sleep(1)
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
        tempimg = capture_frame(rect)
        text = ocr_image(tempimg, reader, QUEREN_RECT)
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