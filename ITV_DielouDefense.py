# 驱入虚空防御挂机

WAVE_COUNT = 4

from Utils.AutoUtils import *
from Utils.IntoTheVoidUtils import *
import random

RENWUWANCHENG_RECT = (0.2, 0, 0.4, 0.2)
QIANWANGMUBIAO_RECT = (0.0, 0.4, 0.2, 0.6)
KAISHIZUOZHAN_RECT = (0.7, 0.9, 0.9, 1.0)
INBATTLE_RECT = (0.7, 0.9, 0.9, 1.0)

hwnd = get_window_handle('驱入虚空')
reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
current_wave = 0
current_stage = 0
while True:
    if current_stage == 0:
        rect = get_window_rect(hwnd)
        img = capture_frame(rect)
        text = ocr_image(img, reader, KAISHIZUOZHAN_RECT)
        bbox, _ = find_text_with_confidence(text, '开始作战')
        if bbox:
            x, y = get_real_click_position(rect, KAISHIZUOZHAN_RECT, img.size, bbox)
            click(hwnd, x, y)
            log('开始作战')
            current_stage = 1
            continue
    if current_stage == 1:
        # 刚进游戏，释放两只金甲虫并跑到第一个目标点
        rect = get_window_rect(hwnd)
        img = capture_frame(rect)
        text = ocr_image(img, reader, INBATTLE_RECT)
        bbox, _ = find_text_with_confidence(text, 'LShift')
        if bbox:
            current_wave = 1
            # 释放两只金甲虫
            key_press(hwnd, 'Q')
            time.sleep(3)
            key_press(hwnd, 'Q')
            log("进入副本")
            time.sleep(3)
            # 开始运动到第一个目标点的位置
            key_down(hwnd, 'w')
            key_down(hwnd, 'a')
            time.sleep(1)
            key_up(hwnd, 'a')
            key_down(hwnd, 'd')
            time.sleep(6.35)
            key_up(hwnd, 'd')
            key_up(hwnd, 'w')
            current_stage = 2
            continue
    if current_stage == 2:
        # 这是在第一个目标点，时刻准备跑向第二个目标点
        rect = get_window_rect(hwnd)
        img = capture_frame(rect)
        text = ocr_image(img, reader, QIANWANGMUBIAO_RECT)
        bbox, _ = find_text_with_confidence(text, '前往目标地点', 0.5)
        print(text)
        if bbox:
            key_down(hwnd, 'w')
            key_down(hwnd, 'a')
            time.sleep(1.5)
            key_up(hwnd, 'a')
            key_down(hwnd, 'd')
            time.sleep(6)
            key_up(hwnd, 'd')
            key_down(hwnd, 'a')
            time.sleep(2.75)
            key_up(hwnd, 'a')
            key_up(hwnd, 'w')
            current_stage = 3
            # 释放两个金甲虫
            key_press(hwnd, 'Q')
            time.sleep(3)
            key_press(hwnd, 'Q')
            continue
    if current_stage == 3:
        # 这是在第二个目标点，视情况决定结束游戏还是跑回第一个目标点
        rect = get_window_rect(hwnd)
        img = capture_frame(rect)
        text = ocr_image(img, reader, RENWUWANCHENG_RECT)
        bbox, _ = find_text_with_confidence(text, '任务完成')
        if bbox:
            if current_wave >= WAVE_COUNT:
                key_press(hwnd, 'esc')
                log(f'结束{WAVE_COUNT}波，重新开始')
                time.sleep(1)
                key_press(hwnd, 'esc')
                time.sleep(1)
                key_press(hwnd, 'r')
                time.sleep(1)
                current_stage = 1
                continue
            else:
                key_press(hwnd, 'c')
                log(f'{current_wave}波结束')
                # 开始往回跑
                key_down(hwnd, 's')
                key_down(hwnd, 'd')
                time.sleep(2.75)
                key_up(hwnd, 'd')
                key_down(hwnd, 'a')
                time.sleep(6)
                key_up(hwnd, 'a')
                key_down(hwnd, 'd')
                time.sleep(1.5)
                key_up(hwnd, 'd')
                key_up(hwnd, 's')
                # 释放两只金甲虫
                key_press(hwnd, 'Q')
                time.sleep(3)
                key_press(hwnd, 'Q')
                # 等待久一点，让怪物刷新出来
                time.sleep(10)
                current_wave += 1
                current_stage = 2
                continue




                
            


