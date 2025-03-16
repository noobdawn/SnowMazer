from enum import Enum
from abc  import ABC, abstractmethod
import Data.AutoData as ad
import Utils.AutoUtils as au
import time

class ActionEnum(Enum):
    # 需要执行的动作
    ACTION_NONE = 0
    ACTION_KEY_DOWN = 1
    ACTION_KEY_UP = 2
    ACTION_KEY_PRESS = 3
    ACTION_MOUSE_DOWN = 4
    ACTION_MOUSE_UP = 5
    ACTION_MOUSE_CLICK = 6
    ACTION_MOUSE_CLICK_OCRAREA = 7
    ACTION_WAIT = 8

class Condition:
    # 操作执行的条件
    CONDITIONS_NONE = 0
    CONDITIONS_OCR_TEXT = 1


class BaseAction:
    def __init__(self,
                    startAction : ActionEnum, startActionParams : dict,
                    endCondition : Condition, endConditionParams : dict,
                    endAction : ActionEnum, endActionParams : dict,
                    hint : str):
        self.startAction = startAction
        self.startActionParams = startActionParams
        self.endCondition = endCondition
        self.endConditionParams = endConditionParams
        self.endAction = endAction
        self.endActionParams = endActionParams
        self.hint = hint
        self.cacheParams = {}
        self.__startActionExecuted = False
        self.__endActionExecuted = False



    def _isConditionMet(self) -> bool:
        if self.endCondition == Condition.CONDITIONS_NONE:
            return True
        elif self.endCondition == Condition.CONDITIONS_OCR_TEXT:
            hwnd = ad.hwnd
            rect = au.get_window_rect(hwnd)
            img = au.capture_frame(rect)
            search_rect = self.endConditionParams['search_rect']
            search_text = self.endConditionParams['search_text']
            confidence = self.endConditionParams.get('confidence', 0.8)
            # start_time = time.time()
            text = au.ocr_image(img, ad.cn_reader, search_rect)
            # print(f'ocr time: {time.time() - start_time}')
            bbox, _ = au.find_text_with_confidence(text, search_text, confidence)
            self.cacheParams['ocr_bbox'] = bbox
            self.cacheParams['img_size'] = img.size
            self.cacheParams['window_rect'] = rect
            return bbox is not None
        return False
        

    @property
    def IsDone(self):
        return self.__endActionExecuted


    # 执行动作
    @abstractmethod
    def execute(self):
        if not self.__startActionExecuted:
            self.onActionStart()
            self.__startActionExecuted = True
        elif self._isConditionMet():
            self.onActionEnd()
            self.__endActionExecuted = True

    def executeAction(self, action : ActionEnum, params : dict):    
        if action == ActionEnum.ACTION_NONE:
            return
        elif action == ActionEnum.ACTION_KEY_DOWN:
            keycodes = params['keycodes']
            for keycode in keycodes:
                au.key_down(ad.hwnd, keycode)
        elif action == ActionEnum.ACTION_KEY_UP:
            keycodes = params['keycodes']
            for keycode in keycodes:
                au.key_up(ad.hwnd, keycode)
        elif action == ActionEnum.ACTION_KEY_PRESS:
            keycodes = params['keycodes']
            for keycode in keycodes:
                au.key_press(ad.hwnd, keycode)
        elif action == ActionEnum.ACTION_MOUSE_DOWN:
            pass
        elif action == ActionEnum.ACTION_MOUSE_UP:
            pass
        elif action == ActionEnum.ACTION_MOUSE_CLICK:
            x, y = params['x'], params['y']
            au.click(ad.hwnd, x, y)
        elif action == ActionEnum.ACTION_MOUSE_CLICK_OCRAREA:
            ocr_bbox = self.cacheParams['ocr_bbox']
            offset_x = params.get('offset_x', 0)
            offset_y = params.get('offset_y', 0)
            search_rect = params.get('search_rect', (0, 0, 1, 1))
            img_size = self.cacheParams['img_size']
            window_rect = self.cacheParams['window_rect']
            x, y = au.get_real_click_position(window_rect, search_rect, img_size, ocr_bbox)
            au.click(ad.hwnd, x, y)
        elif action == ActionEnum.ACTION_WAIT:
            wait_time = params['wait_time']
            time.sleep(wait_time)


    def onActionStart(self):
        self.executeAction(self.startAction, self.startActionParams)


    def onActionEnd(self):
        self.executeAction(self.endAction, self.endActionParams)


MAKE_KEY_DICT = lambda *keys : {'keycodes' : list(keys)}
MAKE_MOUSE_CLICK_DICT = lambda x, y : {'x' : x, 'y' : y}
MAKE_MOUSE_CLICK_OCRAREA_DICT = lambda offset_x, offset_y, search_rect : {'offset_x' : offset_x, 'offset_y' : offset_y, 'search_rect' : search_rect}
MAKE_WAIT_DICT = lambda wait_time : {'wait_time' : wait_time}
MAKE_OCR_DICT = lambda search_rect, search_text, confidence : {'search_rect' : search_rect, 'search_text' : search_text, 'confidence' : confidence}