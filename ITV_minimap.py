import cv2
import numpy as np

def detect_arrow_orientation(minimap_image):
    # 1. 转换为RGB并提取颜色掩膜
    rgb = cv2.cvtColor(minimap_image, cv2.COLOR_BGR2RGB)
    low_rgb = np.array([200, 150, 75])
    high_rgb = np.array([255, 200, 125])
    mask = cv2.inRange(rgb, low_rgb, high_rgb)
    
    # 2. 形态学去噪
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    # 3. 轮廓检测与筛选
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    
    for cnt in contours:
        print(f"cv2.contourArea(cnt): {cv2.contourArea(cnt)}")
    
    valid_contours = [cnt for cnt in contours if 1000 < cv2.contourArea(cnt) < 2000]
    if not valid_contours:
        return None
    
    arrow_contour = max(valid_contours, key=cv2.contourArea)
    
    # 4. 计算角度
    rect = cv2.minAreaRect(arrow_contour)
    angle = rect[-1]
    if angle < -45:
        angle += 90
    final_angle = (angle + 360) % 360
    return final_angle

# 使用示例
minimap = cv2.imread("minimap.png")
angle = detect_arrow_orientation(minimap)
print(f"Player Orientation: {angle} degrees")
