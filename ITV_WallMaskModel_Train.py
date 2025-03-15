import numpy as np

# 读取数据文件
with open('wall_mask.txt', 'r') as f:
    lines = f.readlines()

# 解析数据
X, y = [], []
for line in lines:
    parts = line.strip().split(',')
    r, g, b = map(int, parts[:3])
    label = 1 if parts[3] == '保留' else 0  # 1=墙壁，0=非墙壁
    X.append([r, g, b])
    y.append(label)

X = np.array(X, dtype=np.float32)
y = np.array(y, dtype=np.float32)

# 数据归一化（将RGB值从0-255缩放到0-1）
X = X / 255.0

class BinaryClassifier:
    def __init__(self, input_dim, lr=0.01):
        self.W = np.random.randn(input_dim) * 0.01  # 权重
        self.b = 0.0                               # 偏置
        self.lr = lr                               # 学习率

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def forward(self, X):
        z = np.dot(X, self.W) + self.b
        return self.sigmoid(z)

    def backward(self, X, y_pred, y_true):
        m = X.shape[0]
        dz = y_pred - y_true
        dW = np.dot(X.T, dz) / m
        db = np.sum(dz) / m
        return dW, db

    def update_params(self, dW, db):
        self.W -= self.lr * dW
        self.b -= self.lr * db

    def train(self, X, y, epochs=1000):
        for epoch in range(epochs):
            y_pred = self.forward(X)
            dW, db = self.backward(X, y_pred, y)
            self.update_params(dW, db)
            # 每100次输出一次损失
            if epoch % 100 == 0:
                loss = -np.mean(y * np.log(y_pred) + (1 - y) * np.log(1 - y_pred))
                print(f"Epoch {epoch}, Loss: {loss:.4f}")


model = BinaryClassifier(input_dim=3, lr=0.1)
model.train(X, y, epochs=1000)
np.savez('wall_mask_model.npz', W=model.W, b=model.b)

loaded = np.load('wall_mask_model.npz')
model = BinaryClassifier(input_dim=3)
model.W = loaded['W']
model.b = loaded['b']