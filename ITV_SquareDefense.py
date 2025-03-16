# 驱入虚空防御挂机

WAVE_COUNT = 4
Q_INTERVAL = 7.5

from Utils.AutoUtils import *
from Utils.IntoTheVoidUtils import *
import random

RENWUWANCHENG_RECT = (0.2, 0, 0.4, 0.2)
LUNCI_RECT = (0.0, 0.1, 0.4, 0.55)

hwnd = get_window_handle('驱入虚空')
reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
current_wave = 0
last_q_time = time.time()
while True:
    rect = get_window_rect(hwnd)
    img = capture_frame(rect)

    # 1%的概率跳一下
    # if random.random() < 0.1:
    #     key_press(hwnd, 'space')
    #     log('跳一下')

    current_time = time.time()
    if current_time - last_q_time > Q_INTERVAL:
        # 切回主角释放Q技能后返回
        key_press(hwnd, '1')
        time.sleep(1)
        key_press(hwnd, 'Q')
        time.sleep(3)
        key_press(hwnd, '2')
        last_q_time = current_time
        log('Q技能')

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
            key_press(hwnd, 'esc')
            time.sleep(1)
            key_press(hwnd, 'r')
            time.sleep(10)
