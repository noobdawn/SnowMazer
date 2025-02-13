from SnowUtils import *

WUJINDIKANG_RECT = (0.85, 0.45, 0.95, 0.65)
ZHUNBEIZUOZHAN_RECT = (0.8, 0.85, 1, 1)
QINGXUANZE_RECT = (0.4, 0.05, 0.6, 0.15)
HUOBAN_RECT = (0, 0.5, 1, 0.57)
JINGXIJIANGLI_RECT = (0.4, 0.05, 0.6, 0.15)
QUEDING_RECT = (0.4, 0.8, 0.6, 1)
TUICHU_RECT = (0.4, 0.8, 0.6, 1)

# 伙伴和技能优先级
PRIORITY = [
    # 优先的伙伴
    "零度射线",
    "炽热艺术",
    "灼热烈炎",

    # 优先的增益
    "拦截",
    "再次投掷",
    "扩散灼烧",
    "加量燃烧瓶",

    "多处起爆",
    "扩散爆炸",
    "高亢",
    
    "急速射线",
    "能量稳定",
    "持续灼烧",
]

reader = easyocr.Reader(['ch_sim'])
hwnd = get_window_handle('尘白禁区')
mute = True
mute_game_window("Game.exe", mute)
last_detect_time = time.time()
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
    if now - last_detect_time < 1.0:
        time.sleep(0.001)
        continue
    last_detect_time = now
    if not (is_window_available(hwnd) and win32gui.IsWindowVisible(hwnd)):
        log("未找到窗口，退出程序")
        break
    rect = get_window_rect(hwnd)
    img = capture_frame(rect)
    # 无尽抵抗
    text = ocr_image(img, reader, WUJINDIKANG_RECT)
    bbox = find_text_with_confidence(text, '无尽抵抗', 0.0) # 因为文本和背景花纹融合被检测为符号，故不做置信度限制
    if bbox:
        x, y = get_real_click_position(rect, WUJINDIKANG_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 无尽抵抗")
        continue
    # 准备作战
    text = ocr_image(img, reader, ZHUNBEIZUOZHAN_RECT)
    bbox = find_text_with_confidence(text, '准备作战')
    if bbox:
        x, y = get_real_click_position(rect, ZHUNBEIZUOZHAN_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 准备作战")
        continue
    # 惊喜奖励
    text = ocr_image(img, reader, JINGXIJIANGLI_RECT)
    bbox = find_text_with_confidence(text, '惊喜奖励')
    if bbox:
        x, y = get_real_click_position(rect, JINGXIJIANGLI_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 惊喜奖励")
        continue
    # 退出
    text = ocr_image(img, reader, TUICHU_RECT)
    bbox = find_text_with_confidence(text, '退出')
    if bbox:
        x, y = get_real_click_position(rect, TUICHU_RECT, img.size, bbox)
        click(hwnd, x, y)
        log("检测到 退出")
        continue
    # 请选择
    text = ocr_image(img, reader, QINGXUANZE_RECT)
    bbox = find_text_with_confidence(text, '请选择')
    if bbox:
        # 这里是选择伙伴界面
        text = ocr_image(img, reader, HUOBAN_RECT)
        print(text)
        for p in PRIORITY:
            bbox = find_text_with_confidence(text, p, 0.5)
            if bbox:
                x, y = get_real_click_position(rect, HUOBAN_RECT, img.size, bbox)
                click(hwnd, x, y)
                log(f"检测到{p} 选择增益")
                break
        # 如果都没有找到优先级队列中的技能，那么点击屏幕中间
        x, y = get_real_click_position_nobbox(rect, HUOBAN_RECT, img.size)
        click(hwnd, x, y)
        time.sleep(0.5)
        # 往下挪一点防止干扰下一次截帧
        y = y + 100
        win32api.SetCursorPos((x, y))
        # 确定
        text = ocr_image(img, reader, QUEDING_RECT)
        bbox = find_text_with_confidence(text, '确定')
        if bbox:
            x, y = get_real_click_position(rect, QUEDING_RECT, img.size, bbox)
            click(hwnd, x, y)
            log("检测到 确定")
        continue



        