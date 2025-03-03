# 判定游戏现在处于什么界面，以减少多余的OCR识别
SB_STAGE_LOGIN = 0
SB_STAGE_MAIN = 1

SB_STAGE_SHOP = 2

SB_STAGE_SHOP_BUY = 2.6

from Utils.AutoUtils import *
from dataclasses import dataclass

@dataclass
class SBStageData:
    STAGES = {}
    hwnd = None
    reader = None

_instance = None

def get_data_class(hwnd, reader, stages):
    global _instance
    if _instance is None:
        _instance = SBStageData()
        _instance.hwnd = hwnd
        _instance.reader = reader
        for stage_id, stage in stages.items():
            _instance.STAGES[stage_id] = stage
    return _instance


def buy(rect):
    time.sleep(1)
    img = capture_frame(rect)
    text = ocr_image(img, _instance.reader, (0.6, 0.8, 0.8, 1))
    bbox, _ = find_text_with_confidence(text, '详情', 0.8)
    if bbox is not None:
        text = ocr_image(img, _instance.reader, (0.9, 0.75, 1, 1))
        bbox, _ = find_text_with_confidence(text, '最大', 0.8)
        x, y = get_real_click_position(rect, (0.9, 0.75, 1, 1), img.size, bbox)
        click(_instance.hwnd, x, y)
        time.sleep(0.3)
        x, y = get_real_click_position(rect, (0.9, 0.9, 0.9, 0.9), img.size, bbox)
        click(_instance.hwnd, x, y)
        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.6, 0.8, 0.8, 1))
        bbox, _ = find_text_with_confidence(text, '详情', 0.8)
        if bbox is None:
            log("购买成功")
            key_press(_instance.hwnd, 'esc')
            time.sleep(1)
        else:
            log("购买失败")
            x, y = rect[0] + 100, rect[1] + 100
            click(_instance.hwnd, x, y)
            time.sleep(5)


# 基类
# 其他类继承此类
class SBStage:
    def __init__(self, stage_id, transitions = [], exit_transitions = []):
        self.transitions = transitions
        self.stage_id = stage_id

    def IsMe(self, img):
        pass

    def name(self):
        pass

    def execute(self):
        pass

    def exit(self):
        pass
    
class SBStageLogin(SBStage):
    def __init__(self):
        super().__init__(SB_STAGE_LOGIN, [SB_STAGE_MAIN], [])
        
    def IsMe(self, img):
        text = ocr_image(img, _instance.reader, (0, 0, 0.1, 0.15))
        bbox, _ = find_text_with_confidence(text, '游戏版本', 0.2)
        return bbox is not None
    
    def name(self):
        return '登录界面'
    
    def execute(self):
        rect = get_window_rect(_instance.hwnd)
        click(_instance.hwnd, rect[0] + 100, rect[1] + 100)
        time.sleep(1)

class SBStageMain(SBStage):
    def __init__(self):
        super().__init__(SB_STAGE_MAIN, [SB_STAGE_SHOP], [])
        
    def IsMe(self, img):
        text = ocr_image(img, _instance.reader, (0.9, 0.9, 1, 1))
        bbox, _ = find_text_with_confidence(text, '商店', 0.2)
        return bbox is not None
    
    def name(self):
        return '主界面'
    
class SBStageShop(SBStage):
    def __init__(self):
        super().__init__(SB_STAGE_SHOP, [], [SB_STAGE_MAIN])
        
    def IsMe(self, img):
        text = ocr_image(img, _instance.reader, (0.0, 0.0, 0.15, 1))
        bbox, _ = find_text_with_confidence(text, '活动兑换', 0.2)
        return bbox is not None
    
    def name(self):
        return '商店界面'
    
    def execute(self):
        rect = get_window_rect(_instance.hwnd)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.0, 0.0, 0.15, 1))
        bbox, _ = find_text_with_confidence(text, '地下清理', 0.8)
        if bbox is None:
            bbox, _ = find_text_with_confidence(text, '活动兑换', 0.8)
            x, y = get_real_click_position(rect, (0.0, 0.0, 0.15, 1), img.size, bbox)
            click(_instance.hwnd, x, y)
            time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.0, 0.0, 0.15, 1))
        bbox, _ = find_text_with_confidence(text, '地下清理', 0.8)
        x, y = get_real_click_position(rect, (0.0, 0.0, 0.15, 1), img.size, bbox)
        click(_instance.hwnd, x, y)
        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.15, 0.0, 1, 1))
        bbox, _ = find_text_with_confidence(text, '碳原子板', 0.8)
        if bbox is None:
            log("未找到碳原子板")
        else:
            x, y = get_real_click_position(rect, (0.15, 0.0, 1, 1), img.size, bbox)
            click(_instance.hwnd, x, y)
            # 购买碳原子板

        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.0, 0.0, 0.15, 1))
        bbox, _ = find_text_with_confidence(text, '精神拟境', 0.8)
        x, y = get_real_click_position(rect, (0.0, 0.0, 0.15, 1), img.size, bbox)
        click(_instance.hwnd, x, y)
        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.15, 0.0, 1, 0.6))
        print(text)
        bbox, _ = find_text_with_confidence(text, '量子胞体', 0.4)
        if bbox is None:
            log("未找到量子胞体")
        else:
            x, y = get_real_click_position(rect, (0.15, 0.0, 1, 0.6), img.size, bbox)
            click(_instance.hwnd, x, y)

        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.0, 0.0, 0.15, 1))
        bbox, _ = find_text_with_confidence(text, '循环中心', 0.8)
        x, y = get_real_click_position(rect, (0.0, 0.0, 0.15, 1), img.size, bbox)
        click(_instance.hwnd, x, y)
        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.0, 0.0, 0.15, 1))
        bbox, _ = find_text_with_confidence(text, '后勤人事', 0.8)
        x, y = get_real_click_position(rect, (0.0, 0.0, 0.15, 1), img.size, bbox)
        click(_instance.hwnd, x, y)
        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.15, 0.0, 1, 1))
        bbox, _ = find_text_with_confidence(text, '重修额度', 0.5)
        if bbox is None:
            log("未找到重修额度")
        else:
            x, y = get_real_click_position(rect, (0.15, 0.0, 1, 1), img.size, bbox)
            click(_instance.hwnd, x, y)
            # 重修额度
            buy(rect)

        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.0, 0.0, 0.15, 1))
        bbox, _ = find_text_with_confidence(text, '优质配给', 0.8)
        x, y = get_real_click_position(rect, (0.0, 0.0, 0.15, 1), img.size, bbox)
        click(_instance.hwnd, x, y)
        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.15, 0.0, 1, 0.5))
        bbox, _ = find_text_with_confidence(text, '天启者共鸣誓约', 0.5)
        if bbox is not None:
            x, y = get_real_click_position(rect, (0.15, 0.0, 1, 0.5), img.size, bbox)
            click(_instance.hwnd, x, y)
            log("购买天启者共鸣誓约")
            buy(rect)
        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.15, 0.0, 1, 0.5))
        bbox, _ = find_text_with_confidence(text, '武器定制合约', 0.5)
        if bbox is not None:
            x, y = get_real_click_position(rect, (0.15, 0.0, 1, 0.5), img.size, bbox)
            click(_instance.hwnd, x, y)
            log("购买武器定制合约")
            buy(rect)
        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.15, 0.0, 1, 0.5))
        bbox, _ = find_text_with_confidence(text, '天启者共鸣凭证', 0.5)
        if bbox is not None:
            x, y = get_real_click_position(rect, (0.15, 0.0, 1, 0.5), img.size, bbox)
            click(_instance.hwnd, x, y)
            log("购买天启者共鸣凭证")
            buy(rect)
        time.sleep(1)
        img = capture_frame(rect)
        text = ocr_image(img, _instance.reader, (0.15, 0.0, 1, 0.5))
        bbox, _ = find_text_with_confidence(text, '武器申请书', 0.5)
        if bbox is not None:
            x, y = get_real_click_position(rect, (0.15, 0.0, 1, 0.5), img.size, bbox)
            click(_instance.hwnd, x, y)
            log("购买武器申请书")
            buy(rect)