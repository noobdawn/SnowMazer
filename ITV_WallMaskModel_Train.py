import numpy as np

TRAIN = True
EPOCHS = 10000
MODEL_PATH = 'wall_mask_model.npz'

import numpy as np

class ThreeLayerNN:
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
        return -np.mean(y_true * np.log(y_pred + 1e-8) + (1 - y_true) * np.log(1 - y_pred + 1e-8))
    
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

if TRAIN:
    # 读取数据文件
    with open('wall_mask.csv', 'r') as f:
        lines = f.readlines()

    # 解析数据
    X, y = [], []
    for line in lines:
        parts = line.strip().split(',')
        r, g, b = map(int, parts[:3])
        label = 1 if parts[3] == 'y' else 0  # 1=墙壁，0=非墙壁
        X.append([r, g, b])
        y.append(label)

    X = np.array(X, dtype=np.float32) / 255.0
    y = np.array(y, dtype=np.float32)

    # 洗牌
    indices = np.random.permutation(X.shape[0])
    X = X[indices]
    y = y[indices]

    model = ThreeLayerNN(input_dim=3, lr=0.1)
    model.train(X, y, epochs=EPOCHS)
    np.savez(MODEL_PATH,
                W1 = model.W1, b1 = model.b1,
                W2 = model.W2, b2 = model.b2,
                W3 = model.W3, b3 = model.b3)
else:
    loaded = np.load(MODEL_PATH)
    model = ThreeLayerNN(input_dim=3)
    model.W1 = loaded['W1']
    model.b1 = loaded['b1']
    model.W2 = loaded['W2']
    model.b2 = loaded['b2']
    model.W3 = loaded['W3']
    model.b3 = loaded['b3']

def predict_pixel(rgb):
    rgb_normalized = np.array(rgb) / 255.0
    prob = model.forward(rgb_normalized)
    return 1 if prob > 0.5 else 0

def predict_image(image):
    h, w = image.shape[:2]
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).reshape(-1, 3) / 255.0
    probs = model.forward(rgb)
    mask = (probs > 0.5).astype(np.uint8).reshape(h, w) * 255
    return mask

import cv2
image_path = "test.png"
image = cv2.imread(image_path)
mask = predict_image(image)
masked_image = cv2.bitwise_and(image, image, mask=mask)
cv2.imshow("Masked Image", masked_image)
cv2.waitKey(0)
cv2.destroyAllWindows()

print(predict_pixel([246,189,89]))