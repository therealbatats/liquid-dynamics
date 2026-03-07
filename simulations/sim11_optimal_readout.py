"""
SIM11: Optimal Readout Time Analysis
Simplified: Sweep readout time to find optimal t* ≈ L²/(π²D) for reservoir computing.
Author: Ali Ahmed
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# Physical constants
T = 310.15
c0 = 150.0
D = 1.65e-9  # m²/s

# Domain
L = 50e-9
Nx = 50
dx = L / Nx
x = np.linspace(0, L, Nx)

# Fundamental timescales
tau_diff = L**2 / D
t_star_theory = L**2 / (np.pi**2 * D)

print("SIM11: Optimal Readout Time Analysis")
print(f"Domain: L = {L*1e9:.1f} nm, Nx = {Nx}")
print(f"Diffusion coefficient: D = {D*1e9:.2f}e-9 m²/s")
print(f"Diffusion timescale: τ_diff = L²/D = {tau_diff*1e6:.3f} μs")
print(f"Theoretical optimal: t* = L²/(π²D) = {t_star_theory*1e6:.3f} μs")

# Theme
bg = '#0d1117'
axes_color = '#161b22'
spine_color = '#30363d'
text_color = '#c9d1d9'

def diffusion_profile_1d(x, t, D, c_init, c_bg=None):
    """Analytical solution for 1D diffusion from point source."""
    if c_bg is None:
        c_bg = 1.0
    # Scaled units
    x_norm = x / L
    t_norm = t / tau_diff
    sigma = np.sqrt(4 * D * t / (L**2)) if t > 0 else 1e-6
    # Gaussian diffusion
    c = c_bg + c_init * np.exp(-x_norm**2 / (2 * sigma**2)) / (sigma * np.sqrt(2*np.pi))
    return np.clip(c, 0.01*c0, 20*c0)

def extract_simple_features(c):
    """Extract features from concentration profile."""
    return np.array([
        np.mean(c),
        np.std(c),
        np.max(c) - np.min(c),
        np.sum(np.abs(np.gradient(c))) + 1e-10,
        np.argmax(c) / len(c)  # Position of peak
    ])

def compute_centroid(c, x):
    """Compute center of mass."""
    return np.sum(c * x) / (np.sum(c) + 1e-10)

# Sweep readout times
n_readout = 12
t_readout_values = np.logspace(np.log10(0.01*tau_diff), np.log10(10*tau_diff), n_readout)

accuracies = []
centroids_sine = []
centroids_square = []

print(f"\nGenerating synthetic task data (sine vs square wave)...")

# Simple training: fixed intermediate readout time
t_train = tau_diff
X_train_sine = []
X_train_square = []

np.random.seed(42)
for i in range(3):
    # Sine modulation
    c_sine = diffusion_profile_1d(x, t_train, D, 4*c0)
    X_train_sine.append(extract_simple_features(c_sine))

    # Square wave
    c_square = diffusion_profile_1d(x, t_train, D, 4*c0)
    c_square[x < L/2] *= 0.7  # Asymmetry
    X_train_square.append(extract_simple_features(c_square))

X_train_sine = np.array(X_train_sine)
X_train_square = np.array(X_train_square)

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

print(f"Sweeping {n_readout} readout times...")

for i, t_readout in enumerate(t_readout_values):
    print(f"  {i+1}/{n_readout}: t = {t_readout/tau_diff:.3f}τ_diff")

    # Generate test data at this readout time
    X_test_sine = []
    X_test_square = []
    cents_sine = []
    cents_square = []

    for j in range(3):
        # Sine
        c_sine = diffusion_profile_1d(x, t_readout, D, 4*c0)
        X_test_sine.append(extract_simple_features(c_sine))
        cents_sine.append(compute_centroid(c_sine, x))

        # Square
        c_square = diffusion_profile_1d(x, t_readout, D, 4*c0)
        c_square[x < L/2] *= (0.7 + 0.1*j)
        X_test_square.append(extract_simple_features(c_square))
        cents_square.append(compute_centroid(c_square, x))

    X_test_sine = np.array(X_test_sine)
    X_test_square = np.array(X_test_square)

    # Combine data
    X_train = np.vstack([X_train_sine, X_train_square])
    y_train = np.hstack([np.zeros(len(X_train_sine)), np.ones(len(X_train_square))])

    X_test = np.vstack([X_test_sine, X_test_square])
    y_test = np.hstack([np.zeros(len(X_test_sine)), np.ones(len(X_test_square))])

    # Train and evaluate
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train_scaled, y_train)
    accuracy = clf.score(X_test_scaled, y_test)

    accuracies.append(accuracy)
    centroids_sine.append(np.mean(cents_sine))
    centroids_square.append(np.mean(cents_square))

accuracies = np.array(accuracies)
centroids_sine = np.array(centroids_sine)
centroids_square = np.array(centroids_square)
centroid_separation = np.abs(centroids_sine - centroids_square)

# Find peak accuracy
idx_peak = np.argmax(accuracies)
t_peak = t_readout_values[idx_peak]

print(f"\nPeak accuracy: {accuracies[idx_peak]*100:.1f}% at t = {t_peak*1e6:.3f}μs ({t_peak/tau_diff:.3f}τ_diff)")
print(f"Theoretical optimal: t* = {t_star_theory*1e6:.3f}μs ({t_star_theory/tau_diff:.4f}τ_diff)")

# Get profiles at 3 key times
idx_early = np.argmin(np.abs(t_readout_values - 0.1*tau_diff))
idx_opt = np.argmin(np.abs(t_readout_values - t_star_theory))
idx_late = np.argmin(np.abs(t_readout_values - 2*tau_diff))

c_early_sine = diffusion_profile_1d(x, t_readout_values[idx_early], D, 4*c0)
c_opt_sine = diffusion_profile_1d(x, t_readout_values[idx_opt], D, 4*c0)
c_late_sine = diffusion_profile_1d(x, t_readout_values[idx_late], D, 4*c0)

# Create 4-panel figure
fig = plt.figure(figsize=(14, 10))
fig.patch.set_facecolor(bg)
gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

# Panel 1: Accuracy vs readout time
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(axes_color)
ax1.semilogx(t_readout_values/tau_diff, accuracies*100, 'o-', color='#a8e6cf',
             markersize=8, linewidth=2.5, markeredgecolor=spine_color, markeredgewidth=1)
ax1.axvline(x=1/np.pi**2, color='#ffd93d', linestyle='--', linewidth=2, alpha=0.7, label='t* = L²/(π²D)')
ax1.axvline(x=t_peak/tau_diff, color='#ff6b6b', linestyle=':', linewidth=2, alpha=0.7, label='Peak')
ax1.fill_between([0.5/np.pi**2, 2/np.pi**2], 0, 105, alpha=0.1, color='#ffd93d')
ax1.set_xlabel('Readout Time (τ_diff units)', color=text_color, fontsize=11)
ax1.set_ylabel('Classification Accuracy (%)', color=text_color, fontsize=11)
ax1.set_title('Accuracy vs Readout Time', color=text_color, fontsize=12, fontweight='bold')
ax1.set_ylim([0, 105])
ax1.legend(loc='lower right', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color)
ax1.tick_params(colors=text_color)
for spine in ax1.spines.values():
    spine.set_color(spine_color)
ax1.grid(True, alpha=0.2, color=spine_color)

# Panel 2: Concentration profiles at 3 key times
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(axes_color)
ax2.plot(x*1e9, c_early_sine/c0, label=f'Early (t={t_readout_values[idx_early]*1e6:.2f}μs)',
         color='#ff6b6b', linewidth=2, alpha=0.8)
ax2.plot(x*1e9, c_opt_sine/c0, label=f'Optimal (t={t_readout_values[idx_opt]*1e6:.2f}μs)',
         color='#a8e6cf', linewidth=2.5, alpha=0.9)
ax2.plot(x*1e9, c_late_sine/c0, label=f'Late (t={t_readout_values[idx_late]*1e6:.2f}μs)',
         color='#4ecdc4', linewidth=2, alpha=0.8)
ax2.axhline(y=1, color=spine_color, linestyle='--', alpha=0.5, linewidth=1)
ax2.set_xlabel('Position (nm)', color=text_color, fontsize=11)
ax2.set_ylabel('Concentration (c₀)', color=text_color, fontsize=11)
ax2.set_title('Profiles at Key Readout Times', color=text_color, fontsize=12, fontweight='bold')
ax2.legend(loc='upper right', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color, fontsize=9)
ax2.tick_params(colors=text_color)
for spine in ax2.spines.values():
    spine.set_color(spine_color)
ax2.grid(True, alpha=0.2, color=spine_color)

# Panel 3: Centroid separation (mode analysis)
ax3 = fig.add_subplot(gs[1, 0])
ax3.set_facecolor(axes_color)
ax3.semilogx(t_readout_values/tau_diff, centroid_separation*1e9, 's-', color='#45b7d1',
             markersize=7, linewidth=2.5, markeredgecolor=spine_color, markeredgewidth=1)
ax3.axvline(x=1/np.pi**2, color='#ffd93d', linestyle='--', linewidth=2, alpha=0.7)
ax3.axvline(x=t_peak/tau_diff, color='#ff6b6b', linestyle=':', linewidth=2, alpha=0.7)
ax3.set_xlabel('Readout Time (τ_diff units)', color=text_color, fontsize=11)
ax3.set_ylabel('Centroid Separation (nm)', color=text_color, fontsize=11)
ax3.set_title('Mode Separation vs Time', color=text_color, fontsize=12, fontweight='bold')
ax3.tick_params(colors=text_color)
for spine in ax3.spines.values():
    spine.set_color(spine_color)
ax3.grid(True, alpha=0.2, color=spine_color)

# Panel 4: Processing regimes
ax4 = fig.add_subplot(gs[1, 1])
ax4.set_facecolor(axes_color)

t_regime = t_readout_values / tau_diff
regime_colors = []

for t_norm in t_regime:
    if t_norm < 0.1/np.pi**2:
        regime_colors.append('#ff6b6b')
    elif t_norm < 3/np.pi**2:
        regime_colors.append('#a8e6cf')
    else:
        regime_colors.append('#4ecdc4')

ax4.scatter(t_regime, accuracies*100, c=regime_colors, s=120, alpha=0.7, edgecolor=spine_color, linewidth=1.5)
ax4.axvline(x=1/np.pi**2, color='#ffd93d', linestyle='--', linewidth=2.5, alpha=0.8, label='t* theoretical')
ax4.axhline(y=50, color=spine_color, linestyle=':', alpha=0.5, linewidth=1)

ax4.text(0.05, 95, 'Early\n(t << t*)', transform=ax4.transAxes, color='#ff6b6b',
         fontsize=10, fontweight='bold', ha='left', va='top',
         bbox=dict(boxstyle='round', facecolor=axes_color, edgecolor=spine_color, alpha=0.7))
ax4.text(0.5, 95, 'Optimal\n(t ≈ t*)', transform=ax4.transAxes, color='#a8e6cf',
         fontsize=10, fontweight='bold', ha='center', va='top',
         bbox=dict(boxstyle='round', facecolor=axes_color, edgecolor=spine_color, alpha=0.7))
ax4.text(0.95, 95, 'Late\n(t >> t*)', transform=ax4.transAxes, color='#4ecdc4',
         fontsize=10, fontweight='bold', ha='right', va='top',
         bbox=dict(boxstyle='round', facecolor=axes_color, edgecolor=spine_color, alpha=0.7))

ax4.set_xscale('log')
ax4.set_xlabel('Readout Time (τ_diff units)', color=text_color, fontsize=11)
ax4.set_ylabel('Accuracy (%)', color=text_color, fontsize=11)
ax4.set_title('Processing Regimes', color=text_color, fontsize=12, fontweight='bold')
ax4.set_ylim([0, 105])
ax4.legend(loc='lower center', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color)
ax4.tick_params(colors=text_color)
for spine in ax4.spines.values():
    spine.set_color(spine_color)
ax4.grid(True, alpha=0.2, color=spine_color, which='both')

plt.suptitle('SIM11: Optimal Readout Time for Reservoir Computing',
             fontsize=14, fontweight='bold', color=text_color, y=0.995)

plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim11_optimal_readout.png',
            dpi=150, bbox_inches='tight', facecolor=bg)
print("\nFigure saved: sim11_optimal_readout.png")
plt.close()

print("\n=== SIM11 COMPLETE ===")
