"""
Simulation 15: Feedback and Recurrence in Liquid Dynamics
Demonstrates recurrent behavior in 1D Nernst-Planck system with boundary feedback.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate
from scipy.stats import linregress

# ============================================================================
# Physical Parameters
# ============================================================================
T = 310.15  # Temperature in K
c0 = 150.0  # Reference concentration in mM
D = 1.96e-9  # Diffusion coefficient in m²/s
F = 96485.0  # Faraday constant in C/mol
R = 8.314  # Gas constant in J/(mol·K)
VT = R * T / F  # Thermal voltage in V

# Grid and time parameters
N = 80  # Number of grid points
L = 50e-9  # Domain length in m
dx = L / N
dt_factor = 0.3
dt = dt_factor * dx**2 / (2 * D)
t_total = 600  # Total timesteps

# Electric field and input parameters
phi_amplitude = 0.05  # Electric field amplitude in V/m
A_in = 0.3 * c0  # Input signal amplitude
omega = np.pi / (50 * dt)  # Input frequency
tau_delay = 30  # Feedback delay in timesteps

# Readout window (middle third)
readout_left = N // 3
readout_right = 2 * N // 3

print("=" * 70)
print("SIMULATION 15: FEEDBACK AND RECURRENCE")
print("=" * 70)
print(f"Grid points: {N}, Domain: {L*1e9:.1f} nm")
print(f"Timestep: {dt*1e6:.3f} μs, Total time: {t_total*dt*1e6:.1f} μs")
print(f"Input amplitude: {A_in:.2f} mM, Frequency: {omega:.4f} rad/step")
print(f"Feedback delay: {tau_delay} steps")
print()

# ============================================================================
# Nernst-Planck Solver with Feedback
# ============================================================================

def solve_with_feedback(alpha, label):
    """
    Solve 1D Nernst-Planck with feedback boundary condition.

    Parameters:
    alpha : float
        Feedback gain (dimensionless)
    label : str
        Scenario label

    Returns:
    c_history : (t_total, N) array
        Concentration profile over time
    readout_history : (t_total,) array
        Readout signal (mean concentration in readout window)
    """
    # Initialize concentration field
    c = np.ones(N) * c0
    c_history = np.zeros((t_total, N))
    readout_history = np.zeros(t_total)
    left_bc_history = np.zeros(t_total)

    # Store initial state
    c_history[0] = c.copy()
    readout_history[0] = np.mean(c[readout_left:readout_right])
    left_bc_history[0] = c[0]

    # Diffusion parameter
    D_coeff = D * dt / (dx**2)
    electric_coeff = (D * F / (R * T)) * dt / (2 * dx)

    for t in range(1, t_total):
        # Compute electric field: phi(x,t) = phi_amplitude * sin(pi*x/L) * sin(omega*t)
        x_positions = np.arange(N) * dx
        phi = phi_amplitude * np.sin(np.pi * x_positions / L) * np.sin(omega * t * dt)
        dphi_dx = phi_amplitude * np.cos(np.pi * x_positions / L) * (np.pi / L) * np.sin(omega * t * dt)

        # Compute input signal and readout
        input_signal = A_in * np.sin(omega * t * dt)

        # Readout at current time (before update)
        readout_t = np.mean(c[readout_left:readout_right])
        readout_history[t] = readout_t

        # Feedback term (delayed)
        if t >= tau_delay:
            feedback_term = alpha * readout_history[t - tau_delay]
        else:
            feedback_term = 0.0

        # Left boundary condition: c(0,t) = c0 + A_in*sin(omega*t) + alpha*readout(t-tau_delay)
        c_left = c0 + input_signal + feedback_term
        left_bc_history[t] = c_left

        # Solve Nernst-Planck equation using finite differences
        c_new = c.copy()

        # Interior points (i = 1, ..., N-2)
        for i in range(1, N - 1):
            d2c_dx2 = (c[i+1] - 2*c[i] + c[i-1]) / (dx**2)
            dc_phi = (c[i+1] * dphi_dx[i+1] - c[i-1] * dphi_dx[i-1]) / (2 * dx)
            dc_dt = D * d2c_dx2 - (D * F / (R * T)) * dc_phi
            c_new[i] = c[i] + dc_dt * dt

        # Boundary conditions
        c_new[0] = c_left  # Left BC with feedback
        c_new[N-1] = c0    # Right BC (fixed)

        # Clip to physical bounds
        c_new = np.clip(c_new, 0.01 * c0, 20 * c0)

        c = c_new
        c_history[t] = c.copy()

    return c_history, readout_history, left_bc_history


# ============================================================================
# Run Four Scenarios
# ============================================================================

scenarios = [
    (0.0, "No feedback"),
    (0.05 * c0, "Weak excitatory"),
    (0.20 * c0, "Strong excitatory"),
    (-0.10 * c0, "Inhibitory"),
]

results = {}

for alpha, label in scenarios:
    print(f"Running: {label} (alpha={alpha:.2f})")
    c_hist, readout, left_bc = solve_with_feedback(alpha, label)
    results[label] = {
        'c_history': c_hist,
        'readout': readout,
        'left_bc': left_bc,
        'alpha': alpha
    }

print()

# ============================================================================
# Analysis 1: Memory Capacity (Cross-correlation with Input Signal)
# ============================================================================

input_signal = A_in * np.sin(omega * np.arange(t_total) * dt)

memory_capacities = {}
for label, data in results.items():
    readout = data['readout']

    # Normalize signals
    readout_norm = readout - np.mean(readout)
    readout_norm = readout_norm / (np.std(readout_norm) + 1e-10)
    input_norm = input_signal - np.mean(input_signal)
    input_norm = input_norm / (np.std(input_norm) + 1e-10)

    # Cross-correlation at various delays (0 to 50 steps)
    correlations = []
    for delay in range(0, min(51, t_total)):
        if delay < len(input_norm):
            corr = np.mean(input_norm[:-delay if delay > 0 else len(input_norm)] *
                          readout_norm[delay:])
            correlations.append(abs(corr))

    memory_capacities[label] = np.max(correlations) if correlations else 0.0

# ============================================================================
# Analysis 2: Signal Amplification
# ============================================================================

amplifications = {}
for label, data in results.items():
    readout = data['readout']
    amp = np.std(readout) / (A_in + 1e-10)
    amplifications[label] = amp

# ============================================================================
# Analysis 3: Lyapunov Exponent (Trajectory Divergence)
# ============================================================================

def compute_lyapunov(alpha):
    """
    Compute Lyapunov exponent by running two nearby trajectories.
    """
    # Main trajectory
    c_hist1, _, _ = solve_with_feedback(alpha, "main")

    # Perturbed trajectory (initial condition perturbed)
    np.random.seed(42)
    c_hist2_init = np.ones(N) * c0 + 1e-4 * c0 * np.random.randn(N)
    c_hist2_init = np.clip(c_hist2_init, 0.01 * c0, 20 * c0)

    c = c_hist2_init
    readout_history = np.zeros(t_total)
    readout_history[0] = np.mean(c[readout_left:readout_right])

    divergence = np.zeros(t_total)
    divergence[0] = np.linalg.norm(c_hist1[0] - c) ** 2

    D_coeff = D * dt / (dx**2)

    for t in range(1, t_total):
        x_positions = np.arange(N) * dx
        phi = phi_amplitude * np.sin(np.pi * x_positions / L) * np.sin(omega * t * dt)
        dphi_dx = phi_amplitude * np.cos(np.pi * x_positions / L) * (np.pi / L) * np.sin(omega * t * dt)

        input_signal = A_in * np.sin(omega * t * dt)
        readout_t = np.mean(c[readout_left:readout_right])
        readout_history[t] = readout_t

        if t >= tau_delay:
            feedback_term = alpha * readout_history[t - tau_delay]
        else:
            feedback_term = 0.0

        c_left = c0 + input_signal + feedback_term
        c_new = c.copy()

        for i in range(1, N - 1):
            d2c_dx2 = (c[i+1] - 2*c[i] + c[i-1]) / (dx**2)
            dc_phi = (c[i+1] * dphi_dx[i+1] - c[i-1] * dphi_dx[i-1]) / (2 * dx)
            dc_dt = D * d2c_dx2 - (D * F / (R * T)) * dc_phi
            c_new[i] = c[i] + dc_dt * dt

        c_new[0] = c_left
        c_new[N-1] = c0
        c_new = np.clip(c_new, 0.01 * c0, 20 * c0)

        c = c_new
        divergence[t] = np.linalg.norm(c_hist1[t] - c) ** 2

    # Fit log(divergence) ~ lambda*t
    divergence = np.maximum(divergence, 1e-20)  # Avoid log(0)
    log_div = np.log(divergence)

    # Use middle 60% of data for fitting (avoid initial transient and saturation)
    start_idx = int(0.2 * t_total)
    end_idx = int(0.8 * t_total)
    if end_idx > start_idx + 10:
        t_fit = np.arange(start_idx, end_idx)
        log_div_fit = log_div[start_idx:end_idx]
        slope, _, _, _, _ = linregress(t_fit, log_div_fit)
        lyapunov = slope
    else:
        lyapunov = 0.0

    return lyapunov

lyapunovs = {}
for label, data in results.items():
    alpha = data['alpha']
    lya = compute_lyapunov(alpha)
    lyapunovs[label] = lya

# ============================================================================
# Print Results
# ============================================================================

mc0 = memory_capacities["No feedback"]
mc1 = memory_capacities["Weak excitatory"]
mc2 = memory_capacities["Strong excitatory"]
mc3 = memory_capacities["Inhibitory"]

amp0 = amplifications["No feedback"]
amp1 = amplifications["Weak excitatory"]
amp2 = amplifications["Strong excitatory"]
amp3 = amplifications["Inhibitory"]

lya0 = lyapunovs["No feedback"]
lya1 = lyapunovs["Weak excitatory"]
lya2 = lyapunovs["Strong excitatory"]
lya3 = lyapunovs["Inhibitory"]

print("ANALYSIS RESULTS:")
print("=" * 70)
print(f"No feedback: memory_cap={mc0:.3f}, amplification={amp0:.3f}, lyapunov={lya0:.4f}")
print(f"Weak excitatory (alpha=0.05): memory_cap={mc1:.3f}, amplification={amp1:.3f}, lyapunov={lya1:.4f}")
print(f"Strong excitatory (alpha=0.20): memory_cap={mc2:.3f}, amplification={amp2:.3f}, lyapunov={lya2:.4f}")
print(f"Inhibitory (alpha=-0.10): memory_cap={mc3:.3f}, amplification={amp3:.3f}, lyapunov={lya3:.4f}")
print()
if mc0 > 0:
    print(f"Feedback gain increases memory capacity by: {mc1/mc0:.2f}x (weak), {mc2/mc0:.2f}x (strong)")
else:
    print("Feedback gain increases memory capacity by: inf (weak), inf (strong)")
print()

# ============================================================================
# Plotting
# ============================================================================

fig = plt.figure(figsize=(14, 10), dpi=150)
fig.patch.set_facecolor('#0d1117')

# Color scheme
colors = {
    "No feedback": "#1f77b4",  # blue
    "Weak excitatory": "#ff7f0e",  # orange
    "Strong excitatory": "#2ca02c",  # green
    "Inhibitory": "#d62728",  # red
}

# -------- Panel 1: Readout time series (top, full width) --------
ax1 = plt.subplot(3, 2, (1, 2))
ax1.set_facecolor('#161b22')
ax1.spines['left'].set_color('#c9d1d9')
ax1.spines['bottom'].set_color('#c9d1d9')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.tick_params(colors='#c9d1d9', labelsize=12)

time_array = np.arange(t_total) * dt * 1e6

# Plot input signal (dashed white)
ax1.plot(time_array, input_signal, 'w--', linewidth=1.5, label='Input signal', alpha=0.7)

# Plot readout for each scenario
for label in ["No feedback", "Weak excitatory", "Strong excitatory", "Inhibitory"]:
    ax1.plot(time_array, results[label]['readout'], color=colors[label],
            linewidth=1.5, label=label, alpha=0.8)

ax1.set_xlabel('Time (μs)', color='#c9d1d9', fontsize=12)
ax1.set_ylabel('Concentration (mM)', color='#c9d1d9', fontsize=12)
ax1.set_title('Readout Time Series: All Scenarios', color='#c9d1d9', fontsize=13, fontweight='bold')
ax1.legend(loc='upper right', framealpha=0.9, fontsize=10)
ax1.grid(True, alpha=0.2, color='#c9d1d9')

# -------- Panel 2: Memory capacity bar chart --------
ax2 = plt.subplot(3, 2, 3)
ax2.set_facecolor('#161b22')
ax2.spines['left'].set_color('#c9d1d9')
ax2.spines['bottom'].set_color('#c9d1d9')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.tick_params(colors='#c9d1d9', labelsize=11)

labels_short = ["No FB", "Weak exc", "Strong exc", "Inhibitory"]
mem_cap_vals = [mc0, mc1, mc2, mc3]
bar_colors = [colors["No feedback"], colors["Weak excitatory"],
              colors["Strong excitatory"], colors["Inhibitory"]]

bars = ax2.bar(labels_short, mem_cap_vals, color=bar_colors, alpha=0.8, edgecolor='#c9d1d9', linewidth=1.5)
ax2.set_ylabel('Memory Capacity', color='#c9d1d9', fontsize=11)
ax2.set_title('Memory Capacity', color='#c9d1d9', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.2, color='#c9d1d9', axis='y')

for i, (bar, val) in enumerate(zip(bars, mem_cap_vals)):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{val:.3f}', ha='center', va='bottom', color='#c9d1d9', fontsize=10)

# -------- Panel 3: Lyapunov exponent vs feedback gain --------
ax3 = plt.subplot(3, 2, 4)
ax3.set_facecolor('#161b22')
ax3.spines['left'].set_color('#c9d1d9')
ax3.spines['bottom'].set_color('#c9d1d9')
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
ax3.tick_params(colors='#c9d1d9', labelsize=11)

alphas = [0.0, 0.05*c0, 0.20*c0, -0.10*c0]
lyas = [lya0, lya1, lya2, lya3]
lya_colors = [colors["No feedback"], colors["Weak excitatory"],
              colors["Strong excitatory"], colors["Inhibitory"]]

scatter = ax3.scatter(alphas, lyas, s=150, c=lya_colors, alpha=0.8, edgecolor='#c9d1d9', linewidth=1.5)
ax3.set_xlabel('Feedback gain α', color='#c9d1d9', fontsize=11)
ax3.set_ylabel('Lyapunov exponent λ', color='#c9d1d9', fontsize=11)
ax3.set_title('Lyapunov Exponent vs Feedback', color='#c9d1d9', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.2, color='#c9d1d9')
ax3.axhline(y=0, color='#c9d1d9', linestyle='--', alpha=0.3, linewidth=1)

# -------- Panel 4: Concentration heatmap (strong excitatory) --------
ax4 = plt.subplot(3, 2, 5)
ax4.set_facecolor('#161b22')
ax4.spines['left'].set_color('#c9d1d9')
ax4.spines['bottom'].set_color('#c9d1d9')
ax4.spines['top'].set_visible(False)
ax4.spines['right'].set_visible(False)
ax4.tick_params(colors='#c9d1d9', labelsize=11)

c_heatmap = results["Strong excitatory"]['c_history'].T
x_pos = np.arange(N) * dx * 1e9  # Convert to nm
t_pos = np.arange(t_total) * dt * 1e6  # Convert to μs

im = ax4.imshow(c_heatmap, aspect='auto', origin='lower', cmap='viridis',
                extent=[0, t_total * dt * 1e6, 0, L * 1e9],
                interpolation='bilinear')
ax4.set_xlabel('Time (μs)', color='#c9d1d9', fontsize=11)
ax4.set_ylabel('Position (nm)', color='#c9d1d9', fontsize=11)
ax4.set_title('Concentration (x,t) - Strong Excitatory', color='#c9d1d9', fontsize=12, fontweight='bold')

cbar = plt.colorbar(im, ax=ax4)
cbar.set_label('c (mM)', color='#c9d1d9', fontsize=10)
cbar.ax.tick_params(colors='#c9d1d9', labelsize=10)

# -------- Panel 5: Signal amplification bar chart --------
ax5 = plt.subplot(3, 2, 6)
ax5.set_facecolor('#161b22')
ax5.spines['left'].set_color('#c9d1d9')
ax5.spines['bottom'].set_color('#c9d1d9')
ax5.spines['top'].set_visible(False)
ax5.spines['right'].set_visible(False)
ax5.tick_params(colors='#c9d1d9', labelsize=11)

amp_vals = [amp0, amp1, amp2, amp3]
bars = ax5.bar(labels_short, amp_vals, color=bar_colors, alpha=0.8, edgecolor='#c9d1d9', linewidth=1.5)
ax5.set_ylabel('Amplification (std readout / A_in)', color='#c9d1d9', fontsize=11)
ax5.set_title('Signal Amplification', color='#c9d1d9', fontsize=12, fontweight='bold')
ax5.grid(True, alpha=0.2, color='#c9d1d9', axis='y')

for i, (bar, val) in enumerate(zip(bars, amp_vals)):
    ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{val:.3f}', ha='center', va='bottom', color='#c9d1d9', fontsize=10)

plt.tight_layout()
plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim15_feedback_recurrence.png',
           dpi=150, facecolor='#0d1117', edgecolor='none')
print("Figure saved to: figures/sim15_feedback_recurrence.png")
print()

plt.close()

print("=" * 70)
print("SIMULATION COMPLETE")
print("=" * 70)
