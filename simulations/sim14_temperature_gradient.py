"""
Simulation 14: Temperature Gradient Computing
Spatial temperature variations modulate diffusivity and create additional computational degrees of freedom.
Einstein relation: D(T) = D0 * T/T0
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Physical parameters
T0 = 310.15  # Base temperature (K)
c0 = 150.0   # Base concentration (mol/m³)
D0 = 1.96e-9 # Diffusivity of K+ (m²/s)
F = 96485.0  # Faraday constant
R = 8.314    # Gas constant

# Grid and time parameters
N = 100
L = 100e-9  # Domain size (m)
dx = L / N
dt = 0.3 * (dx**2) / (2 * D0)
n_steps = 500

# Spatial grid
x = np.linspace(0, L, N, endpoint=False)

print("=" * 60)
print("Simulation 14: Temperature Gradient Computing")
print("=" * 60)
print(f"Grid points: {N}, Domain: {L*1e9:.1f} nm, dx: {dx*1e9:.3f} nm")
print(f"Time step: {dt*1e12:.3f} ps, Total steps: {n_steps}")
print(f"D0 = {D0:.3e} m²/s, T0 = {T0:.2f} K, c0 = {c0:.1f} mol/m³")
print()

# ============================================================================
# Define four temperature scenarios
# ============================================================================

def isothermal_T(x):
    """Isothermal case: constant temperature"""
    return np.ones_like(x) * T0

def linear_gradient_T(x):
    """Linear gradient: T varies ±15K across domain"""
    return T0 + 30 * (x / L - 0.5)

def hot_center_T(x):
    """Hot center: Gaussian peak +30K at center"""
    return T0 + 30 * np.exp(-((x - L/2) / (L/8))**2)

def cold_center_T(x):
    """Cold center: Gaussian dip -20K at center"""
    return T0 - 20 * np.exp(-((x - L/2) / (L/8))**2)

scenarios = {
    'isothermal': isothermal_T,
    'linear_gradient': linear_gradient_T,
    'hot_center': hot_center_T,
    'cold_center': cold_center_T
}

scenario_labels = {
    'isothermal': 'Isothermal',
    'linear_gradient': 'Linear Gradient',
    'hot_center': 'Hot Center',
    'cold_center': 'Cold Center'
}

colors = {
    'isothermal': '#0369a1',      # blue
    'linear_gradient': '#ea580c',  # orange
    'hot_center': '#16a34a',       # green
    'cold_center': '#7c3aed'       # purple
}

# ============================================================================
# Simulation function
# ============================================================================

def simulate_scenario(T_func, scenario_name):
    """Run diffusion simulation with spatially-varying diffusivity"""

    # Temperature profile
    T = T_func(x)

    # Diffusivity profile: D(T) = D0 * T/T0
    D = D0 * T / T0
    dD_dx = np.gradient(D, dx)  # Diffusivity gradient

    # Initial condition: sinusoidal perturbation
    c = c0 + 2 * c0 * np.sin(2 * np.pi * x / L)

    # Storage for analysis
    c_history = np.zeros((n_steps + 1, N))
    variance_history = np.zeros(n_steps + 1)
    c_history[0] = c.copy()

    # Compute variance at t=0
    variance_history[0] = np.var(c)

    # Time integration with periodic BCs
    for step in range(n_steps):
        # Compute spatial derivatives with periodic BCs
        dc_dx = np.zeros(N)
        d2c_dx2 = np.zeros(N)

        for i in range(N):
            ip1 = (i + 1) % N
            im1 = (i - 1) % N

            # dc/dx using central difference
            dc_dx[i] = (c[ip1] - c[im1]) / (2 * dx)

            # d²c/dx² using central difference
            d2c_dx2[i] = (c[ip1] - 2*c[i] + c[im1]) / (dx**2)

        # PDE: dc/dt = d/dx[D(x) * dc/dx] = D(x) * d²c/dx² + dD/dx * dc/dx
        dcdt = D * d2c_dx2 + dD_dx * dc_dx

        # Forward Euler update
        c = c + dt * dcdt

        # Store
        c_history[step + 1] = c.copy()
        variance_history[step + 1] = np.var(c)

    return {
        'c_final': c,
        'c_history': c_history,
        'variance_history': variance_history,
        'T': T,
        'D': D,
        'scenario': scenario_name
    }

# ============================================================================
# Run all scenarios
# ============================================================================

results = {}
for scenario_name, T_func in scenarios.items():
    results[scenario_name] = simulate_scenario(T_func, scenario_name)
    print(f"Completed: {scenario_labels[scenario_name]}")

print()

# ============================================================================
# Analysis: compute entropy and decay rates
# ============================================================================

def compute_entropy(c_profile):
    """Compute spatial entropy H = -sum(p*log2(p))"""
    # Normalize to probability distribution
    c_min = c_profile.min()
    c_shifted = c_profile - c_min + 1e-10
    p = c_shifted / c_shifted.sum()

    # Remove zero entries to avoid log(0)
    p = p[p > 0]
    H = -np.sum(p * np.log2(p))
    return H

def exponential_decay(t, A, rate):
    """Exponential decay model"""
    return A * np.exp(-rate * t)

def compute_effective_diffusivity(decay_rate):
    """Effective diffusivity from decay rate: D_eff = -L²/(π² * τ) where τ = 1/rate"""
    if decay_rate > 0:
        tau = 1.0 / decay_rate
        D_eff = -L**2 / (np.pi**2 * tau)
        return D_eff
    else:
        return np.nan

# Compute metrics for each scenario
metrics = {}
for scenario_name in scenarios.keys():
    res = results[scenario_name]

    # Entropy at final time
    h_final = compute_entropy(res['c_final'])

    # Fit exponential decay to variance
    t_steps = np.arange(n_steps + 1)
    t_days = t_steps * dt

    # Only fit where variance is reasonably far from floor
    mask = res['variance_history'] > 1e-6
    if np.sum(mask) > 10:
        try:
            popt, _ = curve_fit(
                exponential_decay,
                t_days[mask],
                res['variance_history'][mask],
                p0=[res['variance_history'][0], 1e5],
                maxfev=10000
            )
            decay_rate = popt[1]
        except:
            decay_rate = 1e5
    else:
        decay_rate = 1e5

    d_eff = compute_effective_diffusivity(decay_rate)

    metrics[scenario_name] = {
        'entropy': h_final,
        'decay_rate': decay_rate,
        'd_eff': d_eff
    }

# ============================================================================
# Print results
# ============================================================================

h_iso = metrics['isothermal']['entropy']
h_lin = metrics['linear_gradient']['entropy']
h_hot = metrics['hot_center']['entropy']
h_cold = metrics['cold_center']['entropy']

d_iso = metrics['isothermal']['d_eff']
d_lin = metrics['linear_gradient']['d_eff']
d_hot = metrics['hot_center']['d_eff']
d_cold = metrics['cold_center']['d_eff']

print("Analysis Results:")
print("-" * 60)
print(f"Isothermal entropy: {h_iso:.3f} bits, D_eff={d_iso:.3e} m^2/s")
print(f"Linear gradient entropy: {h_lin:.3f} bits, D_eff={d_lin:.3e} m^2/s")
print(f"Hot center entropy: {h_hot:.3f} bits, D_eff={d_hot:.3e} m^2/s")
print(f"Cold center entropy: {h_cold:.3f} bits, D_eff={d_cold:.3e} m^2/s")
print(f"Hot/isothermal entropy ratio: {h_hot/h_iso:.3f}")
print(f"Cold/isothermal entropy ratio: {h_cold/h_iso:.3f}")
print()

# ============================================================================
# Create figure with dark theme
# ============================================================================

plt.style.use('dark_background')
fig = plt.figure(figsize=(14, 10), dpi=150)
fig.patch.set_facecolor('#0d1117')

ax_bg_color = '#161b22'
text_color = '#c9d1d9'

# Panel 1: Temperature profiles
ax1 = plt.subplot(2, 3, 1)
ax1.set_facecolor(ax_bg_color)
for scenario_name in scenarios.keys():
    T = results[scenario_name]['T']
    ax1.plot(x*1e9, T, color=colors[scenario_name], linewidth=2.5,
             label=scenario_labels[scenario_name])
ax1.set_xlabel('Position (nm)', color=text_color, fontsize=12)
ax1.set_ylabel('Temperature (K)', color=text_color, fontsize=12)
ax1.set_title('Temperature Profiles', color=text_color, fontsize=13, fontweight='bold')
ax1.legend(fontsize=10, loc='best', framealpha=0.9)
ax1.grid(True, alpha=0.2)
ax1.tick_params(colors=text_color)

# Panel 2: Diffusivity profiles
ax2 = plt.subplot(2, 3, 2)
ax2.set_facecolor(ax_bg_color)
for scenario_name in scenarios.keys():
    D = results[scenario_name]['D']
    ax2.plot(x*1e9, D*1e9, color=colors[scenario_name], linewidth=2.5,
             label=scenario_labels[scenario_name])
ax2.set_xlabel('Position (nm)', color=text_color, fontsize=12)
ax2.set_ylabel('Diffusivity (10⁻⁹ m²/s)', color=text_color, fontsize=12)
ax2.set_title('Diffusivity Profiles D(x)', color=text_color, fontsize=13, fontweight='bold')
ax2.legend(fontsize=10, loc='best', framealpha=0.9)
ax2.grid(True, alpha=0.2)
ax2.tick_params(colors=text_color)

# Panel 3: Final concentration profiles
ax3 = plt.subplot(2, 3, 3)
ax3.set_facecolor(ax_bg_color)
for scenario_name in scenarios.keys():
    c_final = results[scenario_name]['c_final']
    ax3.plot(x*1e9, c_final, color=colors[scenario_name], linewidth=2.5,
             label=scenario_labels[scenario_name])
ax3.set_xlabel('Position (nm)', color=text_color, fontsize=12)
ax3.set_ylabel('Concentration (mol/m³)', color=text_color, fontsize=12)
ax3.set_title('Final Concentration (t=500 steps)', color=text_color, fontsize=13, fontweight='bold')
ax3.legend(fontsize=10, loc='best', framealpha=0.9)
ax3.grid(True, alpha=0.2)
ax3.tick_params(colors=text_color)

# Panel 4: Variance decay
ax4 = plt.subplot(2, 3, 4)
ax4.set_facecolor(ax_bg_color)
t_steps = np.arange(n_steps + 1)
t_days = t_steps * dt
for scenario_name in scenarios.keys():
    var_hist = results[scenario_name]['variance_history']
    ax4.semilogy(t_days*1e12, var_hist, color=colors[scenario_name], linewidth=2.5,
                 label=scenario_labels[scenario_name])
ax4.set_xlabel('Time (ps)', color=text_color, fontsize=12)
ax4.set_ylabel('Variance (mol²/m⁶)', color=text_color, fontsize=12)
ax4.set_title('Variance Decay Over Time', color=text_color, fontsize=13, fontweight='bold')
ax4.legend(fontsize=10, loc='best', framealpha=0.9)
ax4.grid(True, alpha=0.2, which='both')
ax4.tick_params(colors=text_color)

# Panel 5: Entropy comparison (spanning full width)
ax5 = plt.subplot(2, 1, 2)
ax5.set_facecolor(ax_bg_color)
scenario_order = ['isothermal', 'linear_gradient', 'hot_center', 'cold_center']
entropies = [metrics[s]['entropy'] for s in scenario_order]
scenario_names = [scenario_labels[s] for s in scenario_order]
scenario_colors = [colors[s] for s in scenario_order]

bars = ax5.bar(scenario_names, entropies, color=scenario_colors, edgecolor='white', linewidth=1.5, width=0.6)
ax5.set_ylabel('Entropy (bits)', color=text_color, fontsize=12)
ax5.set_title('Final Spatial Entropy Comparison', color=text_color, fontsize=13, fontweight='bold')
ax5.grid(True, alpha=0.2, axis='y')
ax5.tick_params(colors=text_color)

# Add value labels on bars
for bar, entropy in zip(bars, entropies):
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
             f'{entropy:.3f}', ha='center', va='bottom', color=text_color, fontsize=11, fontweight='bold')

plt.tight_layout()

# Save figure
fig_path = '/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim14_temperature_gradient.png'
plt.savefig(fig_path, facecolor='#0d1117', edgecolor='none', dpi=150, bbox_inches='tight')
print(f"Figure saved to: {fig_path}")
plt.close()

print("\n" + "=" * 60)
print("Simulation complete!")
print("=" * 60)
