"""
Simulation 17: Online Learning via Ionic Hebbian Rule
Demonstrates liquid system learning to associate input patterns with target outputs
by adjusting readout weights online using a Hebbian-like update rule.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import special

# ============================================================================
# Physical Parameters
# ============================================================================
T = 310.15          # Temperature (K)
c0 = 150.0          # Baseline concentration (mM)
D = 1.96e-9         # Diffusion coefficient (m^2/s)
F = 96485.0         # Faraday constant (C/mol)
R = 8.314           # Gas constant (J/(mol·K))
VT = R * T / F      # Thermal voltage (V)

# Spatial grid
N = 80              # Number of spatial points
L = 50e-9           # Domain length (m)
dx = L / N          # Spatial step
dt = 0.3 * dx**2 / (2 * D)  # Time step (explicit stability criterion)

# Learning and control parameters
phi_amp = 0.04      # Voltage amplitude (V)
eta = 0.5           # Learning rate (increased for clearer loss reduction)
t_steps_per_trial = 200  # NP steps per trial
n_trials = 100      # Number of learning trials
n_test_trials = 20  # Number of test trials
n_control_trials = 20  # Number of control (random weight) trials

# ============================================================================
# Helper Functions
# ============================================================================

def nernst_planck_step(c, left_bc, right_bc, phi_amp, D, F, R, T, dx, dt, L):
    """
    Execute one step of Nernst-Planck dynamics.
    dc/dt = D*d²c/dx² - (D*F/(R*T))*d/dx(c * dphi/dx)
    phi(x) = phi_amp * sin(pi*x/L)
    dphi/dx = phi_amp * pi/L * cos(pi*x/L)
    """
    # Create x grid (0 to L)
    x = np.linspace(0, L, N)

    # Compute dphi/dx at each point
    dphi_dx = phi_amp * np.pi / L * np.cos(np.pi * x / L)

    # Compute second spatial derivative (diffusion term)
    # Using central differences
    d2c_dx2 = np.zeros(N)
    d2c_dx2[1:-1] = (c[2:] - 2*c[1:-1] + c[:-2]) / (dx**2)
    # Boundary conditions for diffusion term
    d2c_dx2[0] = (c[1] - 2*c[0] + left_bc) / (dx**2)
    d2c_dx2[-1] = (right_bc - 2*c[-1] + c[-2]) / (dx**2)

    # Compute drift term: d/dx(c * dphi/dx)
    # Using central differences for the derivative
    c_dphi = c * dphi_dx
    dc_dphi_dx = np.zeros(N)
    dc_dphi_dx[1:-1] = (c_dphi[2:] - c_dphi[:-2]) / (2*dx)
    # Boundary values (forward/backward difference)
    dc_dphi_dx[0] = (c_dphi[1] - c_dphi[0]) / dx
    dc_dphi_dx[-1] = (c_dphi[-1] - c_dphi[-2]) / dx

    # Full Nernst-Planck equation
    dcdt = D * d2c_dx2 - (D * F / (R * T)) * dc_dphi_dx

    # Update concentration
    c_new = c + dt * dcdt

    # Enforce boundary conditions
    c_new[0] = left_bc
    c_new[-1] = right_bc

    # Clip to physical range
    c_new = np.clip(c_new, 0.01 * c0, 20 * c0)

    return c_new

def run_trial(c_init, left_bc, right_bc, w, t_steps, phi_amp, D, F, R, T, dx, dt, L, eta=None, target=None):
    """
    Run a single trial: evolve NP dynamics and optionally update weights.

    Args:
        c_init: initial concentration profile
        left_bc, right_bc: boundary conditions
        w: weight vector
        t_steps: number of time steps
        eta: learning rate (if None, no learning)
        target: target output (if eta is not None)

    Returns:
        c_final: final concentration profile
        y: output (dot product w·c normalized)
        error: target - y (if eta is not None, else None)
        w_new: updated weights (if eta is not None, else w)
    """
    c = c_init.copy()

    # Run Nernst-Planck dynamics for t_steps
    for _ in range(t_steps):
        c = nernst_planck_step(c, left_bc, right_bc, phi_amp, D, F, R, T, dx, dt, L)

    # Compute output (normalized by concentration magnitude)
    # Use centered, normalized readout to improve stability
    c_norm = c / (c0 + 1e-6)  # Normalize by baseline
    z = np.dot(w, c_norm)  # Raw output
    # Apply tanh to compress to [-1, 1] range
    y = np.tanh(z)

    # Learning update if requested
    if eta is not None and target is not None:
        error = target - y
        # Backprop through tanh: derivative = 1 - y^2
        grad_y_z = 1.0 - y**2
        # Update rule: Δw = eta * error * tanh'(z) * c_norm
        # Normalize by c0 to keep updates reasonable
        w_new = w + eta * error * grad_y_z * c_norm / N
        # Clip weights to prevent explosion
        w_new = np.clip(w_new, -1, 1)
    else:
        error = None
        w_new = w

    return c, y, error, w_new

# ============================================================================
# Main Simulation
# ============================================================================

# Initialize weight vector (very small random values)
w = np.random.randn(N) * 0.001

# Storage for results
errors_A = []
errors_B = []
y_all = []
targets_all = []
trial_indices = []

print("=" * 70)
print("Simulation 17: Online Learning via Ionic Hebbian Rule")
print("=" * 70)
print(f"\nPhysical Parameters:")
print(f"  Temperature: {T} K")
print(f"  Baseline concentration: {c0} mM")
print(f"  Diffusion coefficient: {D} m²/s")
print(f"  Domain length: {L*1e9} nm")
print(f"  Number of grid points: {N}")
print(f"  Time step: {dt} s")
print(f"\nLearning Parameters:")
print(f"  Learning rate (eta): {eta}")
print(f"  Voltage amplitude: {phi_amp} V")
print(f"  Steps per trial: {t_steps_per_trial}")
print(f"  Total trials: {n_trials}")

# Learning phase: 100 trials alternating Pattern A and B
print(f"\n{'Trial':<8} {'Pattern':<10} {'Target':<10} {'Output':<10} {'Error':<10}")
print("-" * 50)

for trial in range(n_trials):
    # Alternate patterns: odd (0-indexed) → Pattern B, even → Pattern A
    if trial % 2 == 0:
        # Pattern A: high left input
        left_bc = c0 + 0.4 * c0
        target = 1.0
        pattern = 'A'
    else:
        # Pattern B: low left input
        left_bc = c0 - 0.2 * c0
        target = -1.0
        pattern = 'B'

    right_bc = c0

    # FRESH START each trial (initialize c = c0 everywhere)
    c_current = np.ones(N) * c0

    # Run trial with learning
    c_current, y, error, w = run_trial(
        c_current, left_bc, right_bc, w, t_steps_per_trial,
        phi_amp, D, F, R, T, dx, dt, L,
        eta=eta, target=target
    )

    # Record results
    y_all.append(y)
    targets_all.append(target)
    trial_indices.append(trial)

    if pattern == 'A':
        errors_A.append(abs(error))
    else:
        errors_B.append(abs(error))

    if trial < 3 or trial % 20 == 19:
        print(f"{trial+1:<8} {pattern:<10} {target:<10.4f} {y:<10.4f} {error:<10.4f}")

print(f"\nLearning phase complete.")

# Extract first and last loss for reporting
initial_loss = abs(y_all[0] - targets_all[0])
final_loss = abs(y_all[-1] - targets_all[-1])

# ============================================================================
# Test Phase: 20 trials with frozen weights (10 Pattern A, 10 Pattern B)
# ============================================================================

test_outputs = []
test_targets = []
test_predictions = []

print(f"\n{'Test Trial':<12} {'Pattern':<10} {'Target':<10} {'Output':<10} {'Prediction':<12} {'Correct':<8}")
print("-" * 60)

for test_trial in range(n_test_trials):
    # Alternate patterns: even index → A, odd → B
    if test_trial % 2 == 0:
        left_bc = c0 + 0.4 * c0
        target = 1.0
        pattern = 'A'
    else:
        left_bc = c0 - 0.2 * c0
        target = -1.0
        pattern = 'B'

    right_bc = c0

    # FRESH START each test trial
    c_test = np.ones(N) * c0

    # Run trial WITHOUT learning (eta=None)
    c_test, y, _, _ = run_trial(
        c_test, left_bc, right_bc, w, t_steps_per_trial,
        phi_amp, D, F, R, T, dx, dt, L,
        eta=None, target=None
    )

    # Classification
    prediction = 1.0 if y > 0 else -1.0
    correct = (prediction == target)

    test_outputs.append(y)
    test_targets.append(target)
    test_predictions.append(prediction)

    print(f"{test_trial+1:<12} {pattern:<10} {target:<10.4f} {y:<10.4f} {prediction:<12.1f} {'✓' if correct else '✗':<8}")

test_accuracy = 100.0 * np.mean([p == t for p, t in zip(test_predictions, test_targets)])

# ============================================================================
# Control Phase: Random weights (no learning)
# ============================================================================

w_random = np.random.randn(N) * 0.01
ctrl_predictions = []
ctrl_targets = []

for ctrl_trial in range(n_control_trials):
    if ctrl_trial % 2 == 0:
        left_bc = c0 + 0.4 * c0
        target = 1.0
    else:
        left_bc = c0 - 0.2 * c0
        target = -1.0

    right_bc = c0

    # FRESH START each control trial
    c_ctrl = np.ones(N) * c0

    c_ctrl, y, _, _ = run_trial(
        c_ctrl, left_bc, right_bc, w_random, t_steps_per_trial,
        phi_amp, D, F, R, T, dx, dt, L,
        eta=None, target=None
    )

    prediction = 1.0 if y > 0 else -1.0
    ctrl_predictions.append(prediction)
    ctrl_targets.append(target)

control_accuracy = 100.0 * np.mean([p == t for p, t in zip(ctrl_predictions, ctrl_targets)])

# ============================================================================
# Print Summary Results
# ============================================================================

print("\n" + "=" * 70)
print("SUMMARY RESULTS")
print("=" * 70)
print(f"Initial loss (trial 1): {initial_loss:.4f}")
print(f"Final loss (trial 100): {final_loss:.4f}")
print(f"Loss reduction: {100*(1-final_loss/initial_loss):.1f}%")
print(f"Test accuracy (learned weights): {test_accuracy:.1f}%")
print(f"Test accuracy (random weights): {control_accuracy:.1f}%")
print(f"Learning improvement: {test_accuracy - control_accuracy:.1f}% over random")
print("=" * 70)

# ============================================================================
# Plotting
# ============================================================================

# Compute rolling mean of errors
def rolling_mean(arr, window=10):
    if len(arr) < window:
        return arr
    return np.convolve(arr, np.ones(window)/window, mode='valid')

errors_A_array = np.array(errors_A)
errors_B_array = np.array(errors_B)

# Interleave A and B errors back into trial order
errors_combined = []
a_idx, b_idx = 0, 0
for trial in range(n_trials):
    if trial % 2 == 0:
        errors_combined.append(errors_A[a_idx])
        a_idx += 1
    else:
        errors_combined.append(errors_B[b_idx])
        b_idx += 1
errors_combined = np.array(errors_combined)

# Rolling mean for each pattern (computed within-pattern)
errors_A_smooth = rolling_mean(errors_A_array, window=10)
errors_B_smooth = rolling_mean(errors_B_array, window=10)

trials_A = np.arange(0, n_trials, 2)[:len(errors_A_smooth)]
trials_B = np.arange(1, n_trials, 2)[:len(errors_B_smooth)]

# Create figure with dark theme
fig = plt.figure(figsize=(14, 9), dpi=150)
fig.patch.set_facecolor('#0d1117')

# Panel 1: Learning curve
ax1 = plt.subplot(2, 2, 1)
ax1.set_facecolor('#161b22')
ax1.plot(trials_A, errors_A_smooth, color='#58a6ff', linewidth=2.5, label='Pattern A (10-trial MA)')
ax1.plot(trials_B, errors_B_smooth, color='#fb8500', linewidth=2.5, label='Pattern B (10-trial MA)')
ax1.axhline(0, color='#c9d1d9', linestyle='-', linewidth=0.8, alpha=0.5)
ax1.set_xlabel('Trial Index', fontsize=12, color='#c9d1d9')
ax1.set_ylabel('Absolute Error', fontsize=12, color='#c9d1d9')
ax1.set_title('Learning Curve', fontsize=13, color='#c9d1d9', fontweight='bold')
ax1.legend(fontsize=10, loc='upper right', facecolor='#161b22', edgecolor='#c9d1d9', labelcolor='#c9d1d9')
ax1.tick_params(colors='#c9d1d9')
for spine in ax1.spines.values():
    spine.set_edgecolor('#444c56')
ax1.grid(True, alpha=0.1, color='#c9d1d9')

# Panel 2: Output vs trial with correctness coloring
ax2 = plt.subplot(2, 2, 2)
ax2.set_facecolor('#161b22')
y_array = np.array(y_all)
targets_array = np.array(targets_all)
predictions_array = np.array([1.0 if y > 0 else -1.0 for y in y_all])
correct = predictions_array == targets_array

ax2.scatter(np.arange(n_trials)[correct], y_array[correct],
           color='#3fb950', s=40, alpha=0.7, label='Correct', zorder=3)
ax2.scatter(np.arange(n_trials)[~correct], y_array[~correct],
           color='#f85149', s=40, alpha=0.7, label='Incorrect', zorder=3)
ax2.axhline(0, color='#c9d1d9', linestyle='--', linewidth=1.5, alpha=0.7, label='Decision boundary')
ax2.set_xlabel('Trial Index', fontsize=12, color='#c9d1d9')
ax2.set_ylabel('Output y', fontsize=12, color='#c9d1d9')
ax2.set_title('Network Output During Learning', fontsize=13, color='#c9d1d9', fontweight='bold')
ax2.legend(fontsize=10, loc='best', facecolor='#161b22', edgecolor='#c9d1d9', labelcolor='#c9d1d9')
ax2.tick_params(colors='#c9d1d9')
for spine in ax2.spines.values():
    spine.set_edgecolor('#444c56')
ax2.grid(True, alpha=0.1, color='#c9d1d9')

# Panel 3: Final weight vector
ax3 = plt.subplot(2, 2, 3)
ax3.set_facecolor('#161b22')
colors_w = ['#58a6ff' if ww >= 0 else '#f85149' for ww in w]
ax3.bar(np.arange(N), w, color=colors_w, width=1.0, edgecolor='none', alpha=0.8)
ax3.set_xlabel('Spatial Position (grid index)', fontsize=12, color='#c9d1d9')
ax3.set_ylabel('Weight w[i]', fontsize=12, color='#c9d1d9')
ax3.set_title('Final Learned Weights', fontsize=13, color='#c9d1d9', fontweight='bold')
ax3.axhline(0, color='#c9d1d9', linestyle='-', linewidth=0.8, alpha=0.5)
ax3.tick_params(colors='#c9d1d9')
for spine in ax3.spines.values():
    spine.set_edgecolor('#444c56')
ax3.grid(True, alpha=0.1, color='#c9d1d9', axis='y')

# Panel 4: Concentration profiles and weight overlay at trial 50
ax4 = plt.subplot(2, 2, 4)
ax4.set_facecolor('#161b22')

# Run two trials at trial 50 to get concentration profiles
c_snap_a = np.ones(N) * c0
left_bc_a = c0 + 0.4 * c0
for _ in range(t_steps_per_trial):
    c_snap_a = nernst_planck_step(c_snap_a, left_bc_a, c0, phi_amp, D, F, R, T, dx, dt, L)

c_snap_b = np.ones(N) * c0
left_bc_b = c0 - 0.2 * c0
for _ in range(t_steps_per_trial):
    c_snap_b = nernst_planck_step(c_snap_b, left_bc_b, c0, phi_amp, D, F, R, T, dx, dt, L)

x_grid = np.linspace(0, L*1e9, N)  # Convert to nm for plotting
ax4.plot(x_grid, c_snap_a, color='#3fb950', linewidth=2.5, label='Pattern A concentration', marker='o', markersize=3, alpha=0.7)
ax4.plot(x_grid, c_snap_b, color='#f85149', linewidth=2.5, label='Pattern B concentration', marker='s', markersize=3, alpha=0.7)

# Plot scaled weight vector as a line
w_scaled = w / np.max(np.abs(w)) * (np.max([c_snap_a.max(), c_snap_b.max()]) - c0) + c0
ax4.plot(x_grid, w_scaled, color='#a371f7', linewidth=2.0, label='Scaled weight vector', linestyle='--', alpha=0.8)

ax4.set_xlabel('Position (nm)', fontsize=12, color='#c9d1d9')
ax4.set_ylabel('Concentration (mM)', fontsize=12, color='#c9d1d9')
ax4.set_title('Concentration Profiles and Learned Weights', fontsize=13, color='#c9d1d9', fontweight='bold')
ax4.legend(fontsize=10, loc='best', facecolor='#161b22', edgecolor='#c9d1d9', labelcolor='#c9d1d9')
ax4.tick_params(colors='#c9d1d9')
for spine in ax4.spines.values():
    spine.set_edgecolor('#444c56')
ax4.grid(True, alpha=0.1, color='#c9d1d9')

plt.tight_layout()
plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim17_online_learning.png',
            facecolor='#0d1117', edgecolor='none', bbox_inches='tight', dpi=150)
print(f"\nFigure saved to: /sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim17_online_learning.png")

plt.close()

print(f"Simulation complete!")
