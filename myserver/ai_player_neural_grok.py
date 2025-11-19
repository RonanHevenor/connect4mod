# simple_torch_xor.py
# Minimal Py How to train a tiny neural network with PyTorch (XOR example)

import torch

# 1. Data - XOR
X = torch.tensor([[0, 0],
                  [0, 1],
                  [1, 0],
                  [1, 1]], dtype=torch.float32)

y = torch.tensor([[0],
                  [1],
                  [1],
                  [0]], dtype=torch.float32)

# 2. Define a super simple 2-layer neural network
class XORNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Linear(2, 8),   # input → hidden
            torch.nn.Sigmoid(),      # activation
            torch.nn.Linear(8, 1),   # hidden → output
            torch.nn.Sigmoid()       # final activation
        )
    
    def forward(self, x):
        return self.layers(x)

model = XORNet()

# 3. Loss and optimizer
criterion = torch.nn.MSELoss()
optimizer = torch.optim.SGD(model.parameters(), lr=10)  # high lr works great here

# 4. Training loop
epochs = 2000
for epoch in range(epochs):
    # Forward pass
    predictions = model(X)
    loss = criterion(predictions, y)
    
    # Backward pass + update
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    
    if epoch % 400 == 0:
        print(f"Epoch {epoch:4d} → Loss: {loss.item():.6f}")

# 5. Final results
print("\nTraining complete! Predictions:")
with torch.no_grad():
    preds = model(X)
    print("Input → Output (rounded) → Expected")
    for i in range(4):
        print(f"{X[i].tolist()} → {preds[i][0]:.4f} ({preds[i][0].round()}) → {y[i][0]}")