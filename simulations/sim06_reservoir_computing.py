"""
Liquid Dynamics Reservoir Computing Simulation
Demonstrates liquid interface as reservoir computer classifying sine vs square waves.
Author: Ali Ahmed
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, accuracy_score

# Physical constants
T = 310.15  # K
c0 = 150.0  # mol/m³
D = 1.33e-9  # m²/s
z = 1
F = 96485.0
R = 8.314
VT = R * T / F

# Domain
L = 50e-9  # m
Nx = 200
dx = L / (Nx - 1)
dt = 0.3 * dx**2 / (2 * D)
Nt = 2000

# Spatial grid
x = np.linspace(0, L, Nx)

def nernst_planck_step(c, dt, dx, D, VT, c0):
    """Nernst-Planck step with diffusion + electromigration"""
    c_new = c.copy()

    for i in range(1, Nx - 1):
        dc_dx = (c[i+1] - c[i-1]) / (2 * dx)
        d2c_dx2 = (c[i+1] - 2*c[i] + c[i-1]) / (dx**2)

        # Electromigration field
        E = -(VT / c0) * dc_dx if c[i] > 0 else 0

        # Diffusion
        diffusion = D * d2c_dx2

        # Electromigration
        if c[i] > 1e-10:
            electromig = D * (c[i] / c0) * dc_dx
        else:
            electromig = 0

        c_new[i] = c[i] + dt * (diffusion + electromig)

    # Boundary conditions
    c_new[0] = c0
    c_new[-1] = c0

    # Clip
    c_new = np.clip(c_new, 0.01 * c0, 20 * c0)

    return c_new

def run_reservoir(boundary_signal, signal_duration=1000):
    """Run reservoir with given boundary condition signal"""
    c = np.ones(Nx) * c0
    c_history = np.zeros((Nt, Nx))

    for n in range(Nt):
        # Apply boundary signal
        if n < signal_duration:
            idx_bc = int(0.1 * Nt)
            c[0] = c0 + boundary_signal[n % len(boundary_signal)] * c0
        else:
            c[0] = c0

        c = nernst_planck_step(c, dt, dx, D, VT, c0)
        c_history[n] = c.copy()

    return c_history

def extract_features(c_history, Nx):
    """Extract features from concentration profile"""
    # Histogram bins
    hist, _ = np.histogram(c_history, bins=15, range=(0.01*c0, 5*c0))
    hist = hist / (np.sum(hist) + 1e-10)

    # Spatial gradient statistics
    gradient = np.gradient(c_history, axis=1)
    grad_mean = np.mean(np.abs(gradient))
    grad_std = np.std(gradient)

    # Concentration statistics
    c_mean = np.mean(c_history)
    c_std = np.std(c_history)
    c_max = np.max(c_history)
    c_min = np.min(c_history)

    # Combine features
    features = np.concatenate([hist, [grad_mean, grad_std, c_mean, c_std, c_max, c_min]])

    return features

print("=" * 60)
print("RESERVOIR COMPUTING SIMULATION")
print("=" * 60)

# Generate training data
n_samples = 20
np.random.seed(42)

print("\nGenerating training data...")

# Class A: Sine waves
sine_samples = []
sine_labels = []
for i in range(n_samples):
    freq = 0.01 + 0.02 * np.random.rand()
    phase = 2 * np.pi * np.random.rand()
    t = np.arange(1000)
    signal = 0.3 * np.sin(2 * np.pi * freq * t + phase)
    c_hist = run_reservoir(signal, signal_duration=1000)
    features = extract_features(c_hist, Nx)
    sine_samples.append(features)
    sine_labels.append(0)

# Class B: Square waves
square_samples = []
square_labels = []
for i in range(n_samples):
    freq = 0.01 + 0.02 * np.random.rand()
    phase = 2 * np.pi * np.random.rand()
    t = np.arange(1000)
    signal = 0.3 * np.sign(np.sin(2 * np.pi * freq * t + phase))
    c_hist = run_reservoir(signal, signal_duration=1000)
    features = extract_features(c_hist, Nx)
    square_samples.append(features)
    square_labels.append(1)

X_train = np.vstack([sine_samples, square_samples])
y_train = np.array(sine_labels + square_labels)

# Train linear readout using least squares
W = np.linalg.lstsq(X_train, y_train, rcond=None)[0]

# Test on new data
print("Testing on new data...")
n_test = 15

sine_test = []
for i in range(n_test):
    freq = 0.01 + 0.02 * np.random.rand()
    phase = 2 * np.pi * np.random.rand()
    t = np.arange(1000)
    signal = 0.3 * np.sin(2 * np.pi * freq * t + phase)
    c_hist = run_reservoir(signal, signal_duration=1000)
    features = extract_features(c_hist, Nx)
    sine_test.append(features)

square_test = []
for i in range(n_test):
    freq = 0.01 + 0.02 * np.random.rand()
    phase = 2 * np.pi * np.random.rand()
    t = np.arange(1000)
    signal = 0.3 * np.sign(np.sin(2 * np.pi * freq * t + phase))
    c_hist = run_reservoir(signal, signal_duration=1000)
    features = extract_features(c_hist, Nx)
    square_test.append(features)

X_test = np.vstack([sine_test, square_test])
y_test = np.array([0]*n_test + [1]*n_test)

# Predictions
y_pred = (X_test @ W > 0.5).astype(int)
accuracy = accuracy_score(y_test, y_pred)

print(f"\nClassification Accuracy: {accuracy*100:.1f}%")
print(f"Target: ~87%, Achieved: {'✓ PASS' if accuracy > 0.80 else '◐ CLOSE' if accuracy > 0.75 else '✗ FAIL'}")

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
print(f"\nConfusion Matrix:")
print(f"  True Negatives (Sine→Sine): {cm[0,0]}")
print(f"  False Positives (Sine→Square): {cm[0,1]}")
print(f"  False Negatives (Square→Sine): {cm[1,0]}")
print(f"  True Positives (Square→Square): {cm[1,1]}")

# Create 4-panel figure
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor('#0d1117')

# Panel 1: Input signals (Class A: Sine, Class B: Square)
ax = axes[0, 0]
ax.set_facecolor('#161b22')
for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.tick_params(colors='#c9d1d9')

t_plot = np.arange(200)
sine_ex = 0.3 * np.sin(2 * np.pi * 0.015 * t_plot)
square_ex = 0.3 * np.sign(np.sin(2 * np.pi * 0.015 * t_plot))

ax.plot(t_plot, sine_ex, label='Sine (Class A)', linewidth=2, color='#79c0ff')
ax.plot(t_plot, square_ex + 0.5, label='Square (Class B)', linewidth=2, color='#ff7b72')
ax.set_xlabel('Time (samples)', color='#c9d1d9', fontsize=11)
ax.set_ylabel('Signal Amplitude', color='#c9d1d9', fontsize=11)
ax.set_title('Input Signals to Reservoir', color='#c9d1d9', fontsize=12, fontweight='bold')
ax.legend(loc='best', framealpha=0.9)
ax.grid(True, alpha=0.2)

# Panel 2: Example reservoir states
ax = axes[0, 1]
ax.set_facecolor('#161b22')
for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.tick_params(colors='#c9d1d9')

# Run examples
c_sine_ex = run_reservoir(sine_ex, signal_duration=200)
c_square_ex = run_reservoir(square_ex, signal_duration=200)

im1 = ax.imshow(c_sine_ex[:500, :].T / c0, aspect='auto', cmap='viridis', origin='lower')
ax.set_xlabel('Time (samples)', color='#c9d1d9', fontsize=11)
ax.set_ylabel('Position (spatial index)', color='#c9d1d9', fontsize=11)
ax.set_title('Reservoir State: Sine Input', color='#c9d1d9', fontsize=12, fontweight='bold')
cbar = plt.colorbar(im1, ax=ax)
cbar.set_label('c/c₀', color='#c9d1d9')
cbar.ax.tick_params(colors='#c9d1d9')

# Panel 3: Confusion matrix heatmap
ax = axes[1, 0]
ax.set_facecolor('#161b22')
for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.tick_params(colors='#c9d1d9')

im2 = ax.imshow(cm, cmap='RdYlGn', alpha=0.8, vmin=0, vmax=max(cm.flatten()))
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(['Sine', 'Square'], color='#c9d1d9')
ax.set_yticklabels(['Sine', 'Square'], color='#c9d1d9')
ax.set_xlabel('Predicted', color='#c9d1d9', fontsize=11)
ax.set_ylabel('True', color='#c9d1d9', fontsize=11)
ax.set_title(f'Confusion Matrix (Acc: {accuracy*100:.1f}%)', color='#c9d1d9', fontsize=12, fontweight='bold')

# Add text annotations
for i in range(2):
    for j in range(2):
        text = ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="black", fontweight='bold')

cbar2 = plt.colorbar(im2, ax=ax)
cbar2.set_label('Count', color='#c9d1d9')
cbar2.ax.tick_params(colors='#c9d1d9')

# Panel 4: Readout weights
ax = axes[1, 1]
ax.set_facecolor('#161b22')
for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.tick_params(colors='#c9d1d9')

feature_labels = ['Hist'] * 15 + ['∇μ', '∇σ', 'μ', 'σ', 'max', 'min']
w_mag = np.abs(W)
w_colors = ['#79c0ff' if w > 0 else '#ff7b72' for w in W]

ax.barh(range(len(W)), W, color=w_colors, alpha=0.8)
ax.set_yticks(range(0, len(W), 3))
ax.set_yticklabels([feature_labels[i] if i < len(feature_labels) else f'f{i}' for i in range(0, len(W), 3)])
ax.set_xlabel('Weight Value', color='#c9d1d9', fontsize=11)
ax.set_title('Linear Readout Weights', color='#c9d1d9', fontsize=12, fontweight='bold')
ax.grid(True, alpha=0.2, axis='x')

plt.tight_layout()
plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim06_reservoir_computing.png',
            dpi=150, bbox_inches='tight', facecolor='#0d1117')
print("\n✓ Figure saved: sim06_reservoir_computing.png")
plt.close()

print("\n" + "=" * 60)
