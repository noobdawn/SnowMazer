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

def click_text(rect, search_region, text, confidence=0.8, click_region=None):
    img = capture_frame(rect)
    text_region = search_region if click_region is None else click_region
    ocr_result = ocr_image(img, _instance.reader, search_region)
    bbox, _ = find_text_with_confidence(ocr_result, text, confidence)
    if bbox:
        x, y = get_real_click_position(rect, text_region, img.size, bbox)
        click(_instance.hwnd, x, y)
        time.sleep(1)
        return True
    return False

def buy(rect):
    time.sleep(1)
    if not click_text(rect, (0.6, 0.8, 0.8, 1), '详情'):
        return
    
    if click_text(rect, (0.9, 0.75, 1, 1), '最大') and \
       click_text(rect, (0.9, 0.9, 0.9, 0.9), ''):  # 确认按钮
        
        time.sleep(1)
        if not click_text(rect, (0.6, 0.8, 0.8, 1), '详情'):
            log("购买成功")
            key_press(_instance.hwnd, 'esc')
        else:
            log("购买失败")
            click(_instance.hwnd, rect[0] + 100, rect[1] + 100)
            time.sleep(5)


# 基类
# 其他类继承此类
class SBStage:
    def __init__(self, stage_id, transitions=None, exit_transitions=None):
        self.transitions = transitions or []
        self.exit_transitions = exit_transitions or []
        self.stage_id = stage_id

    def check_text_in_region(self, img, region, text, confidence=0.2):
        ocr_result = ocr_image(img, _instance.reader, region)
        bbox, _ = find_text_with_confidence(ocr_result, text, confidence)
        return bbox is not None

    def common_click(self, region, text, confidence=0.8):
        rect = get_window_rect(_instance.hwnd)
        return click_text(rect, region, text, confidence)

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
        super().__init__(SB_STAGE_LOGIN, [SB_STAGE_MAIN])

    def IsMe(self, img):
        return self.check_text_in_region(img, (0, 0, 0.1, 0.15), '游戏版本')

    def name(self):
        return '登录界面'

    def execute(self):
        self.common_click((0, 0, 1, 1), '', confidence=0)  # 任意位置点击

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
        self.shop_items = [
            {'category': '活动兑换', 'sub_category': '地下清理', 'items': ['碳原子板']},
            {'category': '精神拟境', 'items': ['量子胞体']},
            {'category': '循环中心', 'sub_category': '后勤人事', 'items': ['重修额度']},
            {'category': '优质配给', 'items': [
                '天启者共鸣誓约',
                '武器定制合约', 
                '天启者共鸣凭证',
                '武器申请书',
                '重修申请',
                '量子胞体',
            ]}
        ]

    def IsMe(self, img):
        return self.check_text_in_region(img, (0.0, 0.0, 0.15, 1), '活动兑换')

    def execute(self):
        rect = get_window_rect(_instance.hwnd)
        
        for section in self.shop_items:
            # 处理主分类
            if not click_text(rect, (0.0, 0.0, 0.15, 1), section['category']):
                continue
                
            # 处理子分类（如果有）
            if hasattr(section, 'sub_category'):
                click_text(rect, (0.0, 0.0, 0.15, 1), section['sub_category'])

            # 处理具体商品
            for item in section['items']:
                if click_text(rect, (0.15, 0.0, 1, 0.5), item):
                    buy(rect)
                    time.sleep(1)

    def name(self):
        return '商店界面'