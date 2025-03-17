import Data.AutoData as ad
from Actions.BaseAction import BaseAction as Action
from Actions.BaseAction import ActionEnum as AE
from Actions.BaseAction import Condition as AC
from Actions.ITVAction import ITVAction
from Actions.ITVAction import ITVCondition as IAC
from Actions.BaseAction import *
from Actions.ITVAction import *
import win32gui
import cv2
import numpy as np
import math
from Utils.AutoUtils import *
from Utils.IntoTheVoidUtils import *
from Utils.ScreenCapturer import ScreenCapturer
import easyocr

WAVE_COUNT = 12


def detect_arrow_orientation(minimap_image):
    # 1. 转换为RGB并提取颜色掩膜
    rgb = cv2.cvtColor(minimap_image, cv2.COLOR_BGR2RGB)
    low_rgb = np.array([200, 150, 75])
    high_rgb = np.array([255, 200, 90])
    mask = cv2.inRange(rgb, low_rgb, high_rgb)
    
    # 2. 形态学去噪
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # 3. 轮廓检测与筛选
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    
    valid_contours = [cnt for cnt in contours if 100 < cv2.contourArea(cnt) ]
    if not valid_contours:
        return None
    
    arrow_contour = max(valid_contours, key=cv2.contourArea)
    
    # 4. 提取箭头主方向（使用PCA分析）
    # 将轮廓点转换为适合PCA的格式
    points = arrow_contour.reshape(-1, 2).astype(np.float32)
    
    # 执行PCA分析
    mean, eigenvectors = cv2.PCACompute(points, mean=None)
    
    # 获取主方向向量
    (vx, vy), (nx, ny) = eigenvectors  # 第一主成分是最大方差方向
    
    # 确定方向向量的正负（通过比较两端点距离质心的长度）
    center = mean[0]
    direction_vector = np.array([vx, vy])
    
    # 生成两个可能的端点
    pt1 = center + direction_vector * 20  # 正方向延伸
    pt2 = center - direction_vector * 20  # 负方向延伸
    
    # 找出实际指向端（距离轮廓点更远的一端）
    max_dist = 0
    far_pt = pt1
    for pt in [pt1, pt2]:
        dist = np.max([np.linalg.norm(p - pt) for p in points])
        if dist > max_dist:
            max_dist = dist
            far_pt = pt
    
    # 计算最终方向向量（从质心指向远端点）
    final_vector = far_pt - center
    
    # 5. 计算角度并转换到标准坐标系（0度指向正东，逆时针增加）
    angle = np.degrees(np.arctan2(-final_vector[1], final_vector[0]))  # y轴取反转换为标准坐标系
    angle = angle % 360  # 规范化到0-360度
    
    # 6. 二次验证（通过凸包检测尖端）
    hull = cv2.convexHull(arrow_contour, returnPoints=False)
    defects = cv2.convexityDefects(arrow_contour, hull)
    
    # 寻找最大的凸缺陷（对应箭头底部凹陷）
    if defects is not None:
        max_defect = max(defects, key=lambda x: x[0][3])
        start, end, far, depth = max_defect[0]
        
        # 根据凸缺陷位置微调角度
        tip_point = tuple(arrow_contour[start][0])
        opposite_vector = np.array(tip_point) - center
        tip_angle = np.degrees(np.arctan2(-opposite_vector[1], opposite_vector[0])) % 360
        
        # 如果两个角度差异较大，使用凸缺陷计算结果
        if abs(angle - tip_angle) > 30:
            angle = tip_angle

    return -angle + 180 - 45

wallmask_model = None
def get_wall_mask(image):
    '''对小地图进行处理，使其更加清晰'''
    global wallmask_model
    if wallmask_model is None:
        wallmask_model = WallMaskModel.load_model("wall_mask_model.npz")
    mask = wallmask_model.predict_image(image)
    # 无视像素小于5的轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 5]
    mask = np.zeros_like(mask)
    cv2.drawContours(mask, valid_contours, -1, 255, -1)
    return mask


def get_distance_from_direction(wall_mask, angle, near, far):
    '''
    从指定的方向获取距离
    :param wall_mask: 一张256x256的墙壁掩膜，二值图像，0表示可通行，255表示墙壁
    :param angle: 方向角度，90度指向正下方，0度指向正右方，-90度指向正上方
    :param near: 检测开始的最近距离
    :param far: 检测结束的最远距离
    '''
    wall_mask = np.asarray(wall_mask)
    center = (128.0, 128.0)  # 浮点型中心坐标
    angle_rad = math.radians(angle)
    
    # 计算方向单位向量（数学坐标系）
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)

    # 配置检测参数
    step = 0.5  # 平衡精度与性能的步长
    max_steps = int((far - near) / step) + 1

    for t in np.linspace(near, far, max_steps):
        # 计算当前检测点坐标
        x = center[0] + dx * t
        y = center[1] + dy * t
        
        # 坐标规范化
        xi, yi = int(round(x)), int(round(y))
        
        # 边界有效性检查
        if 0 <= xi < 256 and 0 <= yi < 256:
            if wall_mask[yi, xi] == 255:
                return t  # 命中返回
        else:
            # 射线完全越界时提前终止
            beyond_x = not (0 <= x < 256)
            beyond_y = not (0 <= y < 256)
            if beyond_x and beyond_y:
                break

    return 256  # 未命中返回


# region 动作队列
ACTION_QUEUE = []
CURRENT_ACTION = None

def whenEnterScene():
    global ACTION_QUEUE
    # 释放Q技能，并等待3秒
    ACTION_QUEUE.append(
        Action(
            AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('q'),
            AC.CONDITIONS_NONE, None,
            AE.ACTION_WAIT, MAKE_WAIT_DICT(3),
            "防守第一个地点——第一次释放金甲虫"))
    # 释放Q技能，并等待3秒
    ACTION_QUEUE.append(
        Action(
            AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('q'),
            AC.CONDITIONS_NONE, None,
            AE.ACTION_WAIT, MAKE_WAIT_DICT(3),
            "防守第一个地点——第二次释放金甲虫"))
    

def gotoFirstDefendPoint():
    global ACTION_QUEUE
    # 直到右侧有足够距离前为止，向左前方移动，延迟0.1秒
    ACTION_QUEUE.append(
        ITVAction(
            AE.ACTION_KEY_DOWN, MAKE_KEY_DICT('a', 'w'),
            IAC.CONDITIONS_RIGHT_DISTANCE_BIGGER_THAN, MAKE_RIGHT_DICT(100),
            AE.ACTION_NONE, None,
            "前往第一个防守地点——向左前方移动，按下按键"))
    ACTION_QUEUE.append(
        Action(
            AE.ACTION_WAIT, MAKE_WAIT_DICT(0.01),
            AC.CONDITIONS_NONE, None,
            AE.ACTION_KEY_UP, MAKE_KEY_DICT('a', 'w'),
            "前往第一个防守地点——向左前方移动，抬起按键"))
    # 直到右侧的距离不足20，向右前方移动
    ACTION_QUEUE.append(
        ITVAction(
            AE.ACTION_KEY_DOWN, MAKE_KEY_DICT('d', 'w'),
            IAC.CONDITIONS_RIGHT_DISTANCE_BELOW, MAKE_RIGHT_DICT(20),
            AE.ACTION_KEY_UP, MAKE_KEY_DICT('d', 'w'),
            "前往第一个防守地点——向右前方移动"))
    

def gotoSecondDefendPoint(wave):
    # 直到上侧的距离不足90，向左前方移动
    ACTION_QUEUE.append(
        ITVAction(
            AE.ACTION_KEY_DOWN, MAKE_KEY_DICT('a', 'w'),
            IAC.CONDITIONS_UP_DISTANCE_BELOW, MAKE_UP_DICT(90),
            AE.ACTION_NONE, None,
            "前往第二个防守地点——向左前方移动，按下按键"))
    ACTION_QUEUE.append(
        Action(
            AE.ACTION_WAIT, MAKE_WAIT_DICT(0.1),
            AC.CONDITIONS_NONE, None,
            AE.ACTION_KEY_UP, MAKE_KEY_DICT('a', 'w'),
            "前往第二个防守地点——向左前方移动，抬起按键"))
    # 直到右侧的距离不足20，向右前方移动
    ACTION_QUEUE.append(
        ITVAction(
            AE.ACTION_KEY_DOWN, MAKE_KEY_DICT('d', 'w'),
            IAC.CONDITIONS_RIGHT_DISTANCE_BELOW, MAKE_RIGHT_DICT(20),
            AE.ACTION_KEY_UP, MAKE_KEY_DICT('d', 'w'),
            "前往第二个防守地点——向右前方移动"))
    # 直到上方的距离不足70，向左前方移动
    ACTION_QUEUE.append(
        ITVAction(
            AE.ACTION_KEY_DOWN, MAKE_KEY_DICT('a', 'w'),
            IAC.CONDITIONS_UP_DISTANCE_BELOW, MAKE_UP_DICT(70),
            AE.ACTION_KEY_UP, MAKE_KEY_DICT('a', 'w'),
            "前往第二个防守地点——向左前方移动"))


def returnToFirstDefendPoint(wave):
    # 直到下方的距离不足20，向右后方移动
    ACTION_QUEUE.append(
        ITVAction(
            AE.ACTION_KEY_DOWN, MAKE_KEY_DICT('d', 's'),
            IAC.CONDITIONS_DOWN_DISTANCE_BELOW, MAKE_DOWN_DICT(20),
            AE.ACTION_KEY_UP, MAKE_KEY_DICT('d', 's'),
            "返回第一个防守地点——向右后方移动"))
    # 直到左侧的距离不足30，向左后方移动
    ACTION_QUEUE.append(
        ITVAction(
            AE.ACTION_KEY_DOWN, MAKE_KEY_DICT('a', 's'),
            IAC.CONDITIONS_LEFT_DISTANCE_BELOW, MAKE_LEFT_DICT(30),
            AE.ACTION_KEY_UP, MAKE_KEY_DICT('a', 's'),
            "返回第一个防守地点——向左后方移动"))
    # 直到下方的距离不足40，向右后方移动
    ACTION_QUEUE.append(
        ITVAction(
            AE.ACTION_KEY_DOWN, MAKE_KEY_DICT('d', 's'),
            IAC.CONDITIONS_DOWN_DISTANCE_BELOW, MAKE_DOWN_DICT(40),
            AE.ACTION_KEY_UP, MAKE_KEY_DICT('d', 's'),
            "返回第一个防守地点——向右后方移动"))     


def castQSkill(wave):
    # 释放Q技能，并等待3秒
    ACTION_QUEUE.append(
        Action(
            AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('q'),
            AC.CONDITIONS_NONE, None,
            AE.ACTION_WAIT, MAKE_WAIT_DICT(3),
            "第一次释放金甲虫"))
    # 释放Q技能，并等待3秒
    ACTION_QUEUE.append(
        Action(
            AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('q'),
            AC.CONDITIONS_NONE, None,
            AE.ACTION_WAIT, MAKE_WAIT_DICT(3),
            "第二次释放金甲虫"))
    if wave >= 4:
        # 释放Q技能，并等待3秒
        ACTION_QUEUE.append(
            Action(
                AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('q'),
                AC.CONDITIONS_NONE, None,
                AE.ACTION_WAIT, MAKE_WAIT_DICT(3),
                "第三次释放金甲虫"))
    if wave >= 8:
        # 释放Q技能，并等待3秒
        ACTION_QUEUE.append(
            Action(
                AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('q'),
                AC.CONDITIONS_NONE, None,
                AE.ACTION_WAIT, MAKE_WAIT_DICT(3),
                "第四次释放金甲虫"))


# 添加动作
def fillActionQueue():
    global ACTION_QUEUE
    gotoFirstDefendPoint()
    for wave in range(WAVE_COUNT):
        # 等待，直到识别出左侧区域有"前往目标地点"的文本
        ACTION_QUEUE.append(
            ITVAction(
                AE.ACTION_NONE, None,
                IAC.CONDITIONS_OCR_TEXT, MAKE_OCR_DICT((0.0, 0.45, 0.2, 0.55), "前往目标地点", 0.3),
                AE.ACTION_NONE, None,
                "等待前往第二个防守地点"))
        gotoSecondDefendPoint(wave)
        castQSkill(wave)
        
        if wave < WAVE_COUNT - 1:
            # 等待，直到识别出上方区域有"任务完成"的文本，然后按C键
            ACTION_QUEUE.append(
                ITVAction(
                    AE.ACTION_NONE, None,
                    IAC.CONDITIONS_OCR_TEXT, MAKE_OCR_DICT((0.2, 0, 0.4, 0.2), "任务完成", 0.3),
                    AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('c'),
                    "防守第二个地点——任务完成"))
            # 等待，直到识别出左侧区域有"前往目标地点"的文本
            ACTION_QUEUE.append(
                ITVAction(
                    AE.ACTION_NONE, None,
                    IAC.CONDITIONS_OCR_TEXT, MAKE_OCR_DICT((0.0, 0.45, 0.2, 0.55), "前往目标地点", 0.3),
                    AE.ACTION_NONE, None,
                    "等待前往第一个防守地点"))
            # 原路返回
            returnToFirstDefendPoint(wave)
            castQSkill(wave)
        else:
            # 等待，直到识别出上方区域有"任务完成"的文本，然后按ESC键
            ACTION_QUEUE.append(
                ITVAction(
                    AE.ACTION_NONE, None,
                    IAC.CONDITIONS_OCR_TEXT, MAKE_OCR_DICT((0.2, 0, 0.4, 0.2), "任务完成", 0.3),
                    AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('esc'),
                    "结束本轮防守"))
            # 等待5秒，然后按ESC键
            ACTION_QUEUE.append(
                Action(
                    AE.ACTION_WAIT, MAKE_WAIT_DICT(5),
                    AC.CONDITIONS_NONE, None,
                    AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('esc'),
                    "结束本轮防守"))
            # 等待3秒，然后按R键
            ACTION_QUEUE.append(
                Action(
                    AE.ACTION_WAIT, MAKE_WAIT_DICT(3),
                    AC.CONDITIONS_NONE, None,
                    AE.ACTION_KEY_PRESS, MAKE_KEY_DICT('r'),
                    "结束本轮防守"))            
            # 等待10秒
            ACTION_QUEUE.append(
                Action(
                    AE.ACTION_WAIT, MAKE_WAIT_DICT(10),
                    AC.CONDITIONS_NONE, None,
                    AE.ACTION_NONE, None,
                    "等待下一轮防守"))
            whenEnterScene()
# endregion



# 主函数
def main():
    # 准备全局数据
    ad.hwnd = win32gui.FindWindow(None, "驱入虚空")    
    if not ad.hwnd:
        print("未找到指定窗口")
        return
    ad.reader = easyocr.Reader(['en', 'ch_sim'], gpu=True)
    
    # 获取窗口样式
    style = get_window_style(ad.hwnd)    
    # 设置窗口位置
    set_window_to_left_top(ad.hwnd)
    # 开始捕获屏幕
    capturer = ScreenCapturer(ad.hwnd)
    capturer.start()

    while True:
        frame = capturer.get_latest_frame()
        if frame is  None:
            continue
        
        # 地图位于左上角的256x256区域
        map_rect = (0, 0, 256, 256)
        map_scale_rect = (0.0, 0.0, 256 / 1600, 256 / 900)
        map_image = crop_image_with_scale(frame, map_scale_rect)
        map_image = cv2.resize(map_image, (256 , 256), interpolation=cv2.INTER_NEAREST)

        wall_mask = get_wall_mask(map_image)
        masked_image = cv2.bitwise_and(map_image, map_image, mask=wall_mask)

        angle = detect_arrow_orientation(map_image)

        right_distance = get_distance_from_direction(wall_mask, 0, 17, 256)
        left_distance = get_distance_from_direction(wall_mask, 180, 17, 256)
        up_distance = get_distance_from_direction(wall_mask, -90, 17, 256)
        down_distance = get_distance_from_direction(wall_mask, 90, 17, 256)

        global ACTION_QUEUE, CURRENT_ACTION
        if CURRENT_ACTION is None:
            if len(ACTION_QUEUE) > 0:
                CURRENT_ACTION = ACTION_QUEUE.pop(0)
                print(f"执行动作：{CURRENT_ACTION.hint}")
            else:
                print("动作队列已空")
                fillActionQueue()
                continue

        if type(CURRENT_ACTION) is ITVAction:
            CURRENT_ACTION.setDistance(right_distance, left_distance, up_distance, down_distance)
        CURRENT_ACTION.execute()
        if CURRENT_ACTION.IsDone:
            CURRENT_ACTION = None

        # 绘制预览窗体
        preview_texture = cv2.cvtColor(wall_mask, cv2.COLOR_GRAY2BGR)            
        cv2.putText(preview_texture, "r: " + str(right_distance), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(preview_texture, "l: " + str(left_distance), (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(preview_texture, "u: " + str(up_distance), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(preview_texture, "d: " + str(down_distance), (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.imshow("map", preview_texture)


        # 将窗口放到目标窗口的右边
        cv2.moveWindow("map", capturer.width, 0)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capturer.stop()
    cv2.destroyAllWindows()



if __name__ == "__main__":
    # 请求管理员权限（可能需要）
    try:
        # time.sleep(5)
        main()
    except Exception as e:
        raise e