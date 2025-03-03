# 驱入虚空防御挂机

WAVE_COUNT = 8
CAST_INTERVAL = 31.5

from Utils.AutoUtils import *
from Utils.IntoTheVoidUtils import *

RENWUWANCHENG_RECT = (0.2, 0, 0.4, 0.2)
LUNCI_RECT = (0.0, 0.1, 0.4, 0.55)

hwnd = get_window_handle('驱入虚空')
reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
current_wave = 0
while True:
    rect = get_window_rect(hwnd)
    img = capture_frame(rect)

    # 识别波数
    text = ocr_image(img, reader, LUNCI_RECT)
    wave = get_wave_count(text)
    if wave is not None:
        wave = int(wave)
        if wave != current_wave:
            current_wave = wave
            log(f'第{current_wave}波开始')

    # WAVE_COUNT波之后任务完成
    text = ocr_image(img, reader, RENWUWANCHENG_RECT)
    bbox, _ = find_text_with_confidence(text, '任务完成')
    if bbox:
        if current_wave < WAVE_COUNT:
            key_press(hwnd, 'c')
            log(f'{current_wave}波结束')
            current_wave += 1
            key_press(hwnd, 'Q')
        else:
            key_press(hwnd, 'esc')
            log(f'结束{WAVE_COUNT}波，重新开始')
            time.sleep(1)
            key_press(hwnd, 'r')
            time.sleep(10)
