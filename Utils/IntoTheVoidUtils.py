from Utils.AutoUtils import *
import re

def get_wave_count(results):
    # 遍历所有识别到的文本块
    for i, (bbox, text, confidence) in enumerate(results):
        if '轮次' in text:
            # 尝试从当前文本块直接提取数字
            match = re.search(r'轮次.\s*(\d+)', text)
            if match:
                return match.group(1)
            
            # 计算当前块的位置信息
            xs = [point[0] for point in bbox]
            ys = [point[1] for point in bbox]
            left = min(xs)
            right = max(xs)
            top = min(ys)
            bottom = max(ys)
            mid_y = (top + bottom) / 2
            
            # 寻找右侧附近的数字块
            for j, (cand_bbox, cand_text, cand_conf) in enumerate(results):
                if i == j:
                    continue  # 跳过自身
                if cand_text.strip().isdigit():
                    # 计算候选块的位置
                    c_xs = [point[0] for point in cand_bbox]
                    c_ys = [point[1] for point in cand_bbox]
                    c_left = min(c_xs)
                    c_right = max(c_xs)
                    c_top = min(c_ys)
                    c_bottom = max(c_ys)
                    c_mid_y = (c_top + c_bottom) / 2
                    
                    # 检查垂直位置是否相近（同一行）
                    if abs(c_mid_y - mid_y) < (bottom - top) * 0.5:
                        # 检查水平位置是否在右侧一定范围内
                        if (c_left > right) and (c_left - right < (right - left) * 2):
                            return cand_text.strip()
    
    return None  # 未找到数字