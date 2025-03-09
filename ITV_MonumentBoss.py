from Utils.AutoUtils import *

RENWUWANCHENG_RECT = (0.2, 0.0, 0.4, 0.2)

hwnd = get_window_handle('驱入虚空')
reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
while True:
    rect = get_window_rect(hwnd)
    img = capture_frame(rect)
    text = ocr_image(img, reader, RENWUWANCHENG_RECT)
    bbox, _ = find_text_with_confidence(text, '任务完成')
    if bbox:
        log("检测到 自动撤离")
        # 按下Esc键
        pyautogui.press('esc')
        # 等待1秒
        time.sleep(1)
        # 按下R键
        pyautogui.press('r')
        # 等待10秒
        time.sleep(9)
        # 长按W键
        pyautogui.keyDown('w')
        time.sleep(2.5)
        # 松开W键
        pyautogui.keyUp('w')
        time.sleep(1)
        # 按下F键
        pyautogui.press('f')
    time.sleep(1.0)