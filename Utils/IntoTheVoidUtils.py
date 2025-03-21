from Utils.AutoUtils import *
import re
import numpy as np
import cv2
from Utils.AutoThread import WorkerThread
import Data.AutoData as ad
from Utils.AutoUtils import *
from Utils.IntoTheVoidUtils import *

class WallMaskModel:
    def __init__(self, input_dim=3, hidden1=16, hidden2=8, lr=0.01):
        # 参数初始化（He初始化）
        self.W1 = np.random.randn(input_dim, hidden1) * np.sqrt(2./input_dim)
        self.b1 = np.zeros(hidden1)
        self.W2 = np.random.randn(hidden1, hidden2) * np.sqrt(2./hidden1)
        self.b2 = np.zeros(hidden2)
        self.W3 = np.random.randn(hidden2, 1) * np.sqrt(2./hidden2)
        self.b3 = np.zeros(1)
        self.lr = lr

    def relu(self, x):
        return np.maximum(0, x)
    
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))
    
    def forward(self, X):
        # 前向传播
        self.z1 = np.dot(X, self.W1) + self.b1
        self.a1 = self.relu(self.z1)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        self.a2 = self.relu(self.z2)
        self.z3 = np.dot(self.a2, self.W3) + self.b3
        self.a3 = self.sigmoid(self.z3)
        return self.a3.squeeze()
    
    def backward(self, X, y):
        m = X.shape[0]
        
        # 输出层梯度
        dz3 = (self.a3 - y.reshape(-1,1)) / m
        dW3 = np.dot(self.a2.T, dz3)
        db3 = np.sum(dz3, axis=0)
        
        # 隐藏层2梯度
        dz2 = np.dot(dz3, self.W3.T) * (self.z2 > 0)
        dW2 = np.dot(self.a1.T, dz2)
        db2 = np.sum(dz2, axis=0)
        
        # 隐藏层1梯度
        dz1 = np.dot(dz2, self.W2.T) * (self.z1 > 0)
        dW1 = np.dot(X.T, dz1)
        db1 = np.sum(dz1, axis=0)
        
        # 参数更新
        self.W3 -= self.lr * dW3
        self.b3 -= self.lr * db3
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1
        
    def compute_loss(self, y_pred, y_true):
        return -np.mean(y_true * np.LOG(y_pred + 1e-8) + (1 - y_true) * np.LOG(1 - y_pred + 1e-8))
    
    def train(self, X, y, epochs=5000, batch_size=32):
        for epoch in range(epochs):
            # 小批量训练
            indices = np.random.permutation(X.shape[0])
            for i in range(0, X.shape[0], batch_size):
                batch_idx = indices[i:i+batch_size]
                X_batch = X[batch_idx]
                y_batch = y[batch_idx]
                
                y_pred = self.forward(X_batch)
                self.backward(X_batch, y_batch)
            
            # 每500次输出损失
            if epoch % 500 == 0:
                y_pred = self.forward(X)
                loss = self.compute_loss(y_pred, y)
                accuracy = np.mean((y_pred > 0.5) == y)
                print(f"Epoch {epoch}, Loss: {loss:.4f}, Accuracy: {accuracy:.2f}")

    @staticmethod
    def load_model(path):
        data = np.load(path)
        model = WallMaskModel(input_dim=3)
        model.W1 = data['W1']
        model.b1 = data['b1']
        model.W2 = data['W2']
        model.b2 = data['b2']
        model.W3 = data['W3']
        model.b3 = data['b3']
        return model
    

    def predict_image(self, image):
        h, w = image.shape[:2]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).reshape(-1, 3) / 255.0
        probs = self.forward(rgb)
        mask = (probs > 0.5).astype(np.uint8).reshape(h, w) * 255
        return mask


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


# region 烽燧广场自动挂机
class SquareDefenseWorker(WorkerThread):
    """烽燧广场自动挂机"""
    def __init__(self, wave, qInterval, needSwitch):
        super().__init__()
        self.wave = wave
        self.qInterval = qInterval
        self.needSwitch = needSwitch


    def _run_job(self):
        RENWUWANCHENG_RECT = (0.2, 0, 0.4, 0.2)
        LUNCI_RECT = (0.0, 0.1, 0.4, 0.55)
        hwnd = get_window_handle('驱入虚空')
        LOG("已搜索到窗体句柄：{hwnd}", hwnd=hwnd, tag="烽燧广场")
        reader = ad.reader
        current_wave = 0
        lastQTime = time.time()
        while not self._stop_event.is_set():
            self._pause_event.wait()           # 如果暂停则阻塞
            rect = get_window_rect(hwnd)
            img = capture_frame(rect)
            currentTime = time.time()
            if currentTime - lastQTime > self.qInterval:
                # 切回主角释放Q技能后返回
                if self.needSwitch:
                    key_press(hwnd, '1')
                    time.sleep(1)
                key_press(hwnd, 'Q')
                time.sleep(3)
                if self.needSwitch:
                    key_press(hwnd, '2')
                lastQTime = currentTime

            # 识别波数
            text = ocr_image(img, reader, LUNCI_RECT)
            wave = get_wave_count(text)
            if wave is not None:
                wave = int(wave)
                if wave != current_wave:
                    current_wave = wave
                    LOG(f'第{current_wave}波开始')


            # WAVE_COUNT波之后任务完成
            text = ocr_image(img, reader, RENWUWANCHENG_RECT)
            bbox, _ = find_text_with_confidence(text, '任务完成')
            if bbox:
                if current_wave < self.wave:
                    key_press(hwnd, 'c')
                    LOG(f'{current_wave}波结束')
                    current_wave += 1
                    key_press(hwnd, 'Q')
                else:
                    key_press(hwnd, 'esc')
                    LOG(f'结束{self.wave}波，重新开始')
                    time.sleep(1)
                    key_press(hwnd, 'esc')
                    time.sleep(1)
                    key_press(hwnd, 'r')
                    time.sleep(10)


def isSquareWorking():
    return ad.threadManager.get_current_worker_class() == SquareDefenseWorker


def startSquareDefense(wave, qInterval, needSwitch):
    ad.threadManager.start_new(SquareDefenseWorker, wave, qInterval, needSwitch)


def stopSquareDefense():
    ad.threadManager.stop()
# endregion