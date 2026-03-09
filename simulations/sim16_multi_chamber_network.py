"""
Liquid Dynamics Simulation 16: Multi-Chamber Ionic Network

A network of 3 coupled ionic chambers in series, analogous to hidden layers
in a neural network. Each chamber computes a Nernst-Planck transformation;
the output of one chamber drives the input of the next.

Physical Basis:
- Nernst-Planck equation: dc/dt = D*d²c/dx² - (D*F/(R*T))*d/dx(c*dphi/dx)
- Modulated electric potential: phi(x,t) = phi_amp*sin(pi*x/L)*sin(omega*t)
- Series coupling: mean(c_i) -> left BC of chamber i+1
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import entropy
import warnings
warnings.filterwarnings('ignore')

# Physical parameters
T = 310.15          # Temperature (K)
c0 = 150.0          # Reference concentration (mM)
F = 96485.0         # Faraday constant (C/mol)
R = 8.314           # Gas constant (J/(mol·K))
VT = R * T / F      # Thermal voltage (~25.7 mV at 310K)

# Diffusion coefficients per chamber
D_list = [1.33e-9, 1.96e-9, 2.03e-9]  # Na+, K+, Cl- (m²/s)

# Spatial discretization
N = 60              # Grid points
L = 50e-9           # Domain length (m)
dx = L / N
dt = 0.3 * dx**2 / (2 * max(D_list))

# Temporal parameters
phi_amp = 0.05      # Potential amplitude (V)
omega = np.pi / (80 * dt)
t_steps = 400

# Time vector
t = np.arange(t_steps) * dt

# Spatial grid
x = np.linspace(0, L, N)

print("=" * 70)
print("Liquid Dynamics Simulation 16: Multi-Chamber Ionic Network")
print("=" * 70)
print(f"Physical parameters: T={T}K, c0={c0}mM, VT={VT:.4f}V")
print(f"Spatial: N={N}, L={L*1e9:.1f}nm, dx={dx*1e9:.4f}nm")
print(f"Temporal: dt={dt*1e12:.2f}ps, omega={omega:.2e}rad/s, steps={t_steps}")
print(f"Potential: phi_amp={phi_amp}V, frequency={omega*dt/(2*np.pi):.4f}Hz")
print("=" * 70)

def nernst_planck_step(c, D, c_left, phi, dt, dx):
    """
    Single time step of Nernst-Planck PDE using finite differences.

    dc/dt = D*d²c/dx² - (D*F/(R*T))*d/dx(c*dphi/dx)

    Args:
        c: concentration profile (N,)
        D: diffusion coefficient
        c_left: left BC value
        phi: potential profile (N,)
        dt, dx: time and space steps

    Returns:
        c_new: updated concentration
    """
    c_new = c.copy()
    Pe = D * F / (R * T)  # electrophoretic strength

    # Interior points (i = 1 to N-2)
    for i in range(1, N - 1):
        # Diffusion term: D * d²c/dx²
        d2c_dx2 = (c[i+1] - 2*c[i] + c[i-1]) / (dx**2)

        # Electrophoresis term: (D*F/(R*T)) * d/dx(c * dphi/dx)
        # Use central differences for dphi/dx
        dphi_dx_left = (phi[i] - phi[i-1]) / dx
        dphi_dx_right = (phi[i+1] - phi[i]) / dx
        c_dphi_left = c[i] * dphi_dx_left
        c_dphi_right = c[i+1] * dphi_dx_right
        d_c_dphi_dx = (c_dphi_right - c_dphi_left) / dx

        dc_dt = D * d2c_dx2 - Pe * d_c_dphi_dx
        c_new[i] = c[i] + dt * dc_dt

    # Left BC: Dirichlet
    c_new[0] = c_left

    # Right BC: Dirichlet at c0
    c_new[-1] = c0

    return c_new

def run_chamber(c_init, D, c_left_func, t_steps):
    """
    Run a single chamber for all time steps.

    Args:
        c_init: initial concentration (N,)
        D: diffusion coefficient
        c_left_func: function(t_idx) -> c_left value
        t_steps: number of time steps

    Returns:
        c_full: concentration history (t_steps, N)
        c_left_history: left BC history (t_steps,)
    """
    c = c_init.copy()
    c_full = np.zeros((t_steps, N))
    c_left_history = np.zeros(t_steps)

    for t_idx in range(t_steps):
        c_left = c_left_func(t_idx)
        c_left_history[t_idx] = c_left

        # Modulated potential
        phi = phi_amp * np.sin(np.pi * x / L) * np.sin(omega * t[t_idx])

        # Update
        c = nernst_planck_step(c, D, c_left, phi, dt, dx)
        c = np.clip(c, 0, None)  # Non-negativity
        c_full[t_idx] = c

    return c_full, c_left_history

# ============================================================================
# Run simulations for 4 different input phase shifts
# ============================================================================

phase_shifts = [0, np.pi/4, np.pi/2, 3*np.pi/4]
results = {}

print("\nRunning multi-chamber network for 4 phase shifts...")

for phi_shift in phase_shifts:
    print(f"\n--- Phase shift: {phi_shift/np.pi:.2f}*pi ---")

    # Chamber 1 (Na+): input with phase shift
    def bc1_func(t_idx):
        return c0 + 0.5 * c0 * np.sin(omega * t[t_idx] + phi_shift)

    c1_init = np.full(N, c0)
    c1_full, c1_left_hist = run_chamber(c1_init, D_list[0], bc1_func, t_steps)
    c1_final = c1_full[-1]

    # Chamber 2 (K+): driven by mean(c1)
    c1_mean = np.mean(c1_full, axis=1)
    def bc2_func(t_idx):
        return c1_mean[t_idx]

    c2_init = np.full(N, c0)
    c2_full, c2_left_hist = run_chamber(c2_init, D_list[1], bc2_func, t_steps)
    c2_final = c2_full[-1]

    # Chamber 3 (Cl-): driven by mean(c2)
    c2_mean = np.mean(c2_full, axis=1)
    def bc3_func(t_idx):
        return c2_mean[t_idx]

    c3_init = np.full(N, c0)
    c3_full, c3_left_hist = run_chamber(c3_init, D_list[2], bc3_func, t_steps)
    c3_final = c3_full[-1]

    results[phi_shift] = {
        'c1_final': c1_final,
        'c2_final': c2_final,
        'c3_final': c3_final,
        'c1_full': c1_full,
        'c2_full': c2_full,
        'c3_full': c3_full,
        'c1_left_hist': c1_left_hist,
        'c2_left_hist': c2_left_hist,
        'c3_left_hist': c3_left_hist,
    }

    print(f"  Chamber 1 final: mean={c1_final.mean():.2f}, std={c1_final.std():.2f}")
    print(f"  Chamber 2 final: mean={c2_final.mean():.2f}, std={c2_final.std():.2f}")
    print(f"  Chamber 3 final: mean={c3_final.mean():.2f}, std={c3_final.std():.2f}")

# ============================================================================
# Analysis: Transformation Depth
# ============================================================================

print("\n" + "=" * 70)
print("Analysis: Transformation Depth")
print("=" * 70)

# For phi=0 case (baseline)
phi_0_results = results[0]

# Input signal variation to chamber 1
c1_input_hist = np.array([results[phi]['c1_left_hist'] for phi in phase_shifts])
c1_input_variation = c1_input_hist - c0
c1_input_std = np.std(c1_input_variation)

# Transformation depth for chamber 1
c1_outputs = np.array([results[phi]['c1_final'] for phi in phase_shifts])
c1_output_variation = c1_outputs - c0
c1_output_std = np.mean(np.std(c1_output_variation, axis=1))
td1 = c1_output_std / (c1_input_std + 1e-10)

# Transformation depth for chamber 2
c2_outputs = np.array([results[phi]['c2_final'] for phi in phase_shifts])
c2_output_variation = c2_outputs - c0
c2_output_std = np.mean(np.std(c2_output_variation, axis=1))

c2_input_hist = np.array([results[phi]['c2_left_hist'] for phi in phase_shifts])
c2_input_variation = c2_input_hist - c0
c2_input_std = np.std(c2_input_variation)
td2 = c2_output_std / (c2_input_std + 1e-10)

# Transformation depth for chamber 3
c3_outputs = np.array([results[phi]['c3_final'] for phi in phase_shifts])
c3_output_variation = c3_outputs - c0
c3_output_std = np.mean(np.std(c3_output_variation, axis=1))

c3_input_hist = np.array([results[phi]['c3_left_hist'] for phi in phase_shifts])
c3_input_variation = c3_input_hist - c0
c3_input_std = np.std(c3_input_variation)
td3 = c3_output_std / (c3_input_std + 1e-10)

print(f"C1 input std: {c1_input_std:.4f}, output std: {c1_output_std:.4f}")
print(f"C2 input std: {c2_input_std:.4f}, output std: {c2_output_std:.4f}")
print(f"C3 input std: {c3_input_std:.4f}, output std: {c3_output_std:.4f}")

# ============================================================================
# Analysis: Network Separation Gain
# ============================================================================

print("\n" + "=" * 70)
print("Analysis: Network Separation Gain")
print("=" * 70)

# Pairwise separation for input (chamber 1 final profiles)
c1_finals = np.array([results[phi]['c1_final'] for phi in phase_shifts])
input_separation = 0.0
n_pairs = 0
for i in range(len(phase_shifts)):
    for j in range(i+1, len(phase_shifts)):
        dist = np.linalg.norm(c1_finals[i] - c1_finals[j])**2
        input_separation += dist
        n_pairs += 1
input_separation /= n_pairs

# Pairwise separation for output (chamber 3 final profiles)
c3_finals = np.array([results[phi]['c3_final'] for phi in phase_shifts])
output_separation = 0.0
for i in range(len(phase_shifts)):
    for j in range(i+1, len(phase_shifts)):
        dist = np.linalg.norm(c3_finals[i] - c3_finals[j])**2
        output_separation += dist
output_separation /= n_pairs

sep = (output_separation + 1e-10) / (input_separation + 1e-10)

print(f"Input (C1) pairwise separation: {input_separation:.6f}")
print(f"Output (C3) pairwise separation: {output_separation:.6f}")

# ============================================================================
# Analysis: Layer Entropy (for phi=0 case)
# ============================================================================

print("\n" + "=" * 70)
print("Analysis: Layer Entropy (phi=0 case)")
print("=" * 70)

def compute_entropy(profile, n_bins=15):
    """Compute entropy of concentration profile."""
    hist, _ = np.histogram(profile, bins=n_bins, range=(0, c0*2))
    hist = hist[hist > 0]
    p = hist / hist.sum()
    return entropy(p, base=2)

phi_0_c1 = results[0]['c1_full'][-1]
phi_0_c2 = results[0]['c2_full'][-1]
phi_0_c3 = results[0]['c3_full'][-1]

h1 = compute_entropy(phi_0_c1)
h2 = compute_entropy(phi_0_c2)
h3 = compute_entropy(phi_0_c3)

print(f"Layer 1 entropy: {h1:.3f} bits (profile std: {phi_0_c1.std():.3f})")
print(f"Layer 2 entropy: {h2:.3f} bits (profile std: {phi_0_c2.std():.3f})")
print(f"Layer 3 entropy: {h3:.3f} bits (profile std: {phi_0_c3.std():.3f})")

# ============================================================================
# Print Results (as specified)
# ============================================================================

print("\n" + "=" * 70)
print("FINAL RESULTS")
print("=" * 70)
print(f"Chamber 1 transform depth: {td1:.3f}")
print(f"Chamber 2 transform depth: {td2:.3f}")
print(f"Chamber 3 transform depth: {td3:.3f}")
print(f"Network separation gain: {sep:.3f}x")
print(f"Layer 1 entropy: {h1:.3f} bits")
print(f"Layer 2 entropy: {h2:.3f} bits")
print(f"Layer 3 entropy: {h3:.3f} bits")
print("=" * 70)

# ============================================================================
# Plotting
# ============================================================================

colors = ['#58a6ff', '#79c0ff', '#d29922', '#fb8500']
fig = plt.figure(figsize=(14, 10), dpi=150, facecolor='#0d1117')

# Panel 1: Input signal over time (4 phase values)
ax1 = plt.subplot(3, 2, 1)
ax1.set_facecolor('#161b22')
for i, phi_shift in enumerate(phase_shifts):
    c1_left = results[phi_shift]['c1_left_hist']
    ax1.plot(t*1e9, c1_left, color=colors[i], linewidth=1.5,
             label=f'φ={phi_shift/np.pi:.2f}π')
ax1.axhline(c0, color='#30363d', linestyle='--', linewidth=0.8, alpha=0.5)
ax1.set_xlabel('Time (ns)', color='#c9d1d9', fontsize=11)
ax1.set_ylabel('Left BC (mM)', color='#c9d1d9', fontsize=11)
ax1.set_title('Input Signal: Chamber 1 Left BC', color='#c9d1d9', fontsize=12, fontweight='bold')
ax1.legend(loc='best', fontsize=9, framealpha=0.9)
ax1.tick_params(colors='#c9d1d9', labelsize=10)
ax1.grid(True, alpha=0.1, color='#30363d')

# Panel 2: Chamber 1 final profiles (4 phases)
ax2 = plt.subplot(3, 2, 2)
ax2.set_facecolor('#161b22')
for i, phi_shift in enumerate(phase_shifts):
    c1_final = results[phi_shift]['c1_final']
    ax2.plot(x*1e9, c1_final, color=colors[i], linewidth=2,
             label=f'φ={phi_shift/np.pi:.2f}π')
ax2.axhline(c0, color='#30363d', linestyle='--', linewidth=0.8, alpha=0.5)
ax2.set_xlabel('Position (nm)', color='#c9d1d9', fontsize=11)
ax2.set_ylabel('Concentration (mM)', color='#c9d1d9', fontsize=11)
ax2.set_title('Chamber 1 Final Profiles (Na+)', color='#c9d1d9', fontsize=12, fontweight='bold')
ax2.legend(loc='best', fontsize=9, framealpha=0.9)
ax2.tick_params(colors='#c9d1d9', labelsize=10)
ax2.grid(True, alpha=0.1, color='#30363d')

# Panel 3: Chamber 2 final profiles (4 phases)
ax3 = plt.subplot(3, 2, 3)
ax3.set_facecolor('#161b22')
for i, phi_shift in enumerate(phase_shifts):
    c2_final = results[phi_shift]['c2_final']
    ax3.plot(x*1e9, c2_final, color=colors[i], linewidth=2,
             label=f'φ={phi_shift/np.pi:.2f}π')
ax3.axhline(c0, color='#30363d', linestyle='--', linewidth=0.8, alpha=0.5)
ax3.set_xlabel('Position (nm)', color='#c9d1d9', fontsize=11)
ax3.set_ylabel('Concentration (mM)', color='#c9d1d9', fontsize=11)
ax3.set_title('Chamber 2 Final Profiles (K+)', color='#c9d1d9', fontsize=12, fontweight='bold')
ax3.legend(loc='best', fontsize=9, framealpha=0.9)
ax3.tick_params(colors='#c9d1d9', labelsize=10)
ax3.grid(True, alpha=0.1, color='#30363d')

# Panel 4: Chamber 3 final profiles (4 phases) — shows separation
ax4 = plt.subplot(3, 2, 4)
ax4.set_facecolor('#161b22')
for i, phi_shift in enumerate(phase_shifts):
    c3_final = results[phi_shift]['c3_final']
    ax4.plot(x*1e9, c3_final, color=colors[i], linewidth=2,
             label=f'φ={phi_shift/np.pi:.2f}π', marker='o', markersize=3,
             markevery=6, alpha=0.85)
ax4.axhline(c0, color='#30363d', linestyle='--', linewidth=0.8, alpha=0.5)
ax4.set_xlabel('Position (nm)', color='#c9d1d9', fontsize=11)
ax4.set_ylabel('Concentration (mM)', color='#c9d1d9', fontsize=11)
ax4.set_title('Chamber 3 Final Profiles (Cl-) — Output Separation',
              color='#c9d1d9', fontsize=12, fontweight='bold')
ax4.legend(loc='best', fontsize=9, framealpha=0.9)
ax4.tick_params(colors='#c9d1d9', labelsize=10)
ax4.grid(True, alpha=0.1, color='#30363d')

# Panel 5: Transformation depth bar chart
ax5 = plt.subplot(3, 2, 5)
ax5.set_facecolor('#161b22')
chambers = ['Chamber 1\n(Na+)', 'Chamber 2\n(K+)', 'Chamber 3\n(Cl-)']
depths = [td1, td2, td3]
bars = ax5.bar(chambers, depths, color=['#58a6ff', '#79c0ff', '#fb8500'],
               edgecolor='#30363d', linewidth=1.5, alpha=0.9)
ax5.axhline(1.0, color='#30363d', linestyle='--', linewidth=0.8, alpha=0.5)
ax5.set_ylabel('Transform Depth', color='#c9d1d9', fontsize=11)
ax5.set_title('Transformation Depth per Chamber', color='#c9d1d9', fontsize=12, fontweight='bold')
ax5.tick_params(colors='#c9d1d9', labelsize=10)
ax5.grid(True, alpha=0.1, axis='y', color='#30363d')
for bar, depth in zip(bars, depths):
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height, f'{depth:.3f}',
             ha='center', va='bottom', color='#c9d1d9', fontsize=10, fontweight='bold')

# Panel 6: Layer entropy comparison
ax6 = plt.subplot(3, 2, 6)
ax6.set_facecolor('#161b22')
layers = ['Layer 1\n(Na+)', 'Layer 2\n(K+)', 'Layer 3\n(Cl-)']
entropies = [h1, h2, h3]
bars = ax6.bar(layers, entropies, color=['#58a6ff', '#79c0ff', '#fb8500'],
               edgecolor='#30363d', linewidth=1.5, alpha=0.9)
ax6.set_ylabel('Entropy (bits)', color='#c9d1d9', fontsize=11)
ax6.set_title('Layer Entropy (φ=0 case)', color='#c9d1d9', fontsize=12, fontweight='bold')
ax6.tick_params(colors='#c9d1d9', labelsize=10)
ax6.grid(True, alpha=0.1, axis='y', color='#30363d')
for bar, ent in zip(bars, entropies):
    height = bar.get_height()
    ax6.text(bar.get_x() + bar.get_width()/2., height, f'{ent:.3f}',
             ha='center', va='bottom', color='#c9d1d9', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim16_multi_chamber_network.png',
            facecolor='#0d1117', edgecolor='none', bbox_inches='tight', dpi=150)
print("\nFigure saved to: sim16_multi_chamber_network.png")
plt.close()

print("\nSimulation complete!")
