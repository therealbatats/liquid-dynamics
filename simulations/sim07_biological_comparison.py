"""
Liquid Dynamics vs Biological Neuron Comparison
Compare Liquid Computer to Hodgkin-Huxley biological neuron.
Author: Ali Ahmed
"""

import numpy as np
import matplotlib.pyplot as plt

# Physical constants for liquid
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
dx_liquid = dx  # For consistency
dt_liquid = 0.3 * dx**2 / (2 * D)
Nt = 5000

x = np.linspace(0, L, Nx)

def nernst_planck_step(c, dt, dx, D, VT, c0):
    """Nernst-Planck step"""
    c_new = c.copy()

    for i in range(1, Nx - 1):
        dc_dx = (c[i+1] - c[i-1]) / (2 * dx)
        d2c_dx2 = (c[i+1] - 2*c[i] + c[i-1]) / (dx**2)

        E = -(VT / c0) * dc_dx if c[i] > 0 else 0
        diffusion = D * d2c_dx2

        if c[i] > 1e-10:
            electromig = D * (c[i] / c0) * dc_dx
        else:
            electromig = 0

        c_new[i] = c[i] + dt * (diffusion + electromig)

    c_new[0] = c0
    c_new[-1] = c0
    c_new = np.clip(c_new, 0.01 * c0, 20 * c0)

    return c_new

def run_liquid_simulation(pulse_amplitude=2*c0, pulse_start=1000, pulse_duration=500):
    """Run liquid interface simulation with voltage pulse"""
    c = np.ones(Nx) * c0
    c_history = np.zeros((Nt, Nx))
    v_liquid = np.zeros(Nt)  # Readout voltage proxy

    for n in range(Nt):
        # Apply pulse at boundary
        if pulse_start < n < pulse_start + pulse_duration:
            c[0] = pulse_amplitude
        else:
            c[0] = c0

        c = nernst_planck_step(c, dt_liquid, dx_liquid, D, VT, c0)
        c_history[n] = c.copy()

        # Readout as voltage proxy (concentration gradient)
        center_idx = Nx // 2
        v_liquid[n] = (c[center_idx] - c0) / c0 * 100  # mV scale

    return c_history, v_liquid

# ============================================================================
# Hodgkin-Huxley Model
# ============================================================================

def alpha_m(V):
    """Rate constant m (sodium activation)"""
    return 0.1 * (V + 40) / (1 - np.exp(-(V + 40) / 10))

def beta_m(V):
    """Rate constant m"""
    return 4 * np.exp(-(V + 65) / 18)

def alpha_h(V):
    """Rate constant h (sodium inactivation)"""
    return 0.07 * np.exp(-(V + 65) / 20)

def beta_h(V):
    """Rate constant h"""
    return 1 / (1 + np.exp(-(V + 35) / 10))

def alpha_n(V):
    """Rate constant n (potassium activation)"""
    return 0.01 * (V + 55) / (1 - np.exp(-(V + 55) / 10))

def beta_n(V):
    """Rate constant n"""
    return 0.125 * np.exp(-(V + 65) / 80)

def run_hodgkin_huxley(I_stim=10, stim_start=1000, stim_duration=500):
    """Run Hodgkin-Huxley model"""
    # Parameters (mS/cm², mV, µF/cm²)
    gNa = 120.0
    gK = 36.0
    gL = 0.3
    ENa = 50.0
    EK = -77.0
    EL = -54.4
    Cm = 1.0

    # Initial conditions
    V = -65.0  # Resting potential
    m = alpha_m(V) / (alpha_m(V) + beta_m(V))
    h = alpha_h(V) / (alpha_h(V) + beta_h(V))
    n = alpha_n(V) / (alpha_n(V) + beta_n(V))

    V_history = np.zeros(Nt)
    m_history = np.zeros(Nt)
    h_history = np.zeros(Nt)
    n_history = np.zeros(Nt)

    dt_hh = 0.01  # ms

    for t_idx in range(Nt):
        # Stimulus current
        I_ext = I_stim if stim_start < t_idx < stim_start + stim_duration else 0

        # Conductances
        I_Na = gNa * m**3 * h * (V - ENa)
        I_K = gK * n**4 * (V - EK)
        I_L = gL * (V - EL)

        # Voltage equation
        dV_dt = (I_ext - I_Na - I_K - I_L) / Cm
        V = V + dt_hh * dV_dt

        # Gating variables
        dm_dt = alpha_m(V) * (1 - m) - beta_m(V) * m
        m = m + dt_hh * dm_dt

        dh_dt = alpha_h(V) * (1 - h) - beta_h(V) * h
        h = h + dt_hh * dh_dt

        dn_dt = alpha_n(V) * (1 - n) - beta_n(V) * n
        n = n + dt_hh * dn_dt

        # Store history
        V_history[t_idx] = V
        m_history[t_idx] = m
        h_history[t_idx] = h
        n_history[t_idx] = n

    return V_history, m_history, h_history, n_history

print("=" * 60)
print("LIQUID vs BIOLOGICAL NEURON COMPARISON")
print("=" * 60)

# Run liquid simulation
print("\nRunning liquid interface simulation...")
c_hist, v_liquid = run_liquid_simulation(pulse_amplitude=3*c0, pulse_start=1000, pulse_duration=500)

# Run Hodgkin-Huxley
print("Running Hodgkin-Huxley model...")
V_hh, m_hh, h_hh, n_hh = run_hodgkin_huxley(I_stim=10, stim_start=1000, stim_duration=500)

# Analysis
print("\n" + "-" * 60)
print("VOLTAGE RESPONSE ANALYSIS")
print("-" * 60)

# Time window
t_window = range(900, 3000)
t_ms = np.arange(len(t_window))

# Peak detection
v_hh_peak = np.max(V_hh[t_window])
v_hh_resting = V_hh[900]
v_liquid_peak = np.max(v_liquid[t_window])

print(f"Hodgkin-Huxley:")
print(f"  Resting potential: {v_hh_resting:.2f} mV")
print(f"  Peak voltage: {v_hh_peak:.2f} mV")
print(f"  Amplitude: {v_hh_peak - v_hh_resting:.2f} mV")
print(f"\nLiquid Interface:")
print(f"  Peak readout: {v_liquid_peak:.2f} (normalized units)")
print(f"  Amplitude ratio (L/HH): {v_liquid_peak / (v_hh_peak - v_hh_resting):.2f}")

# Time constants
print(f"\n" + "-" * 60)
print("TEMPORAL DYNAMICS")
print("-" * 60)

# Recovery time (50% recovery from peak)
v_hh_50 = v_hh_resting + 0.5 * (v_hh_peak - v_hh_resting)
peak_idx_hh = 1500 + np.argmax(V_hh[1500:])
recovery_hh = np.where(V_hh[peak_idx_hh:] < v_hh_50)[0]
tau_hh = recovery_hh[0] * 0.01 if len(recovery_hh) > 0 else 0

v_liquid_50 = 0.5 * v_liquid_peak
peak_idx_liquid = 1500 + np.argmax(v_liquid[1500:])
recovery_liquid = np.where(v_liquid[peak_idx_liquid:] < v_liquid_50)[0]
tau_liquid = recovery_liquid[0] * dt_liquid * 1e9 if len(recovery_liquid) > 0 else 0

print(f"Hodgkin-Huxley recovery time (50%): {tau_hh:.2f} ms")
print(f"Liquid interface recovery time: {tau_liquid*1e6:.2f} µs (= {tau_liquid*1e9:.1f} ns)")

# Energy comparison
print(f"\n" + "-" * 60)
print("ENERGY CONSIDERATIONS")
print("-" * 60)

# HH energy dissipation (proportional to I²)
I_Na = 120.0 * m_hh**3 * h_hh * (V_hh - 50.0)
I_K = 36.0 * n_hh**4 * (V_hh + 77.0)
I_L = 0.3 * (V_hh + 54.4)
I_total = I_Na + I_K + I_L
energy_hh = np.sum(I_total**2)

# Liquid energy (proportional to concentration gradient)
gradients = np.gradient(c_hist, axis=1)
energy_liquid = np.sum(gradients**2)

print(f"HH energy dissipation (integrated): {energy_hh:.2e}")
print(f"Liquid energy dissipation (integrated): {energy_liquid:.2e}")

# ============================================================================
# Create 4-panel figure
# ============================================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor('#0d1117')

t_plot = np.arange(Nt) * dt_liquid * 1e6  # Convert to µs

# Panel 1: Voltage traces
ax = axes[0, 0]
ax.set_facecolor('#161b22')
for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.tick_params(colors='#c9d1d9')

ax2 = ax.twinx()
ax2.set_facecolor('#161b22')
ax2.tick_params(colors='#c9d1d9')

ax.plot(t_plot, V_hh, label='Hodgkin-Huxley', linewidth=2.5, color='#79c0ff')
ax2.plot(t_plot, v_liquid, label='Liquid Interface', linewidth=2.5, color='#ff7b72', linestyle='--')

ax.set_xlabel('Time (µs)', color='#c9d1d9', fontsize=11)
ax.set_ylabel('Membrane Potential (mV)', color='#79c0ff', fontsize=11)
ax2.set_ylabel('Readout Signal (norm.)', color='#ff7b72', fontsize=11)
ax.set_title('Voltage Response Comparison', color='#c9d1d9', fontsize=12, fontweight='bold')
ax.tick_params(axis='y', labelcolor='#79c0ff')
ax2.tick_params(axis='y', labelcolor='#ff7b72')
ax.grid(True, alpha=0.2)

# Combined legend
lines1, labels1 = ax.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9)

# Panel 2: Ion concentration / Gating variables
ax = axes[0, 1]
ax.set_facecolor('#161b22')
for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.tick_params(colors='#c9d1d9')

# Plot gating variables
ax.plot(t_plot[::10], m_hh[::10], label='m (Na activation)', linewidth=2, color='#79c0ff', alpha=0.8)
ax.plot(t_plot[::10], h_hh[::10], label='h (Na inactivation)', linewidth=2, color='#ff7b72', alpha=0.8)
ax.plot(t_plot[::10], n_hh[::10], label='n (K activation)', linewidth=2, color='#d29922', alpha=0.8)

ax.set_xlabel('Time (µs)', color='#c9d1d9', fontsize=11)
ax.set_ylabel('Gating Variable (0-1)', color='#c9d1d9', fontsize=11)
ax.set_title('HH Gating Variables', color='#c9d1d9', fontsize=12, fontweight='bold')
ax.set_ylim(-0.05, 1.05)
ax.legend(loc='best', fontsize=9, framealpha=0.9)
ax.grid(True, alpha=0.2)

# Panel 3: Ion concentration profile (liquid)
ax = axes[1, 0]
ax.set_facecolor('#161b22')
for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.tick_params(colors='#c9d1d9')

# Sample time points
t_samples = [1000, 1500, 2000, 3000]
colors_sample = ['#79c0ff', '#58a6ff', '#ff7b72', '#d29922']

for t_idx, color in zip(t_samples, colors_sample):
    ax.plot(x * 1e9, c_hist[t_idx] / c0, label=f't={t_idx*dt_liquid*1e9:.1f} ns',
            linewidth=2, color=color, alpha=0.8)

ax.axhline(y=1, color='#30363d', linestyle='--', linewidth=1, alpha=0.5)
ax.set_xlabel('Position (nm)', color='#c9d1d9', fontsize=11)
ax.set_ylabel('Concentration (c/c₀)', color='#c9d1d9', fontsize=11)
ax.set_title('Liquid Interface: Ion Profiles', color='#c9d1d9', fontsize=12, fontweight='bold')
ax.legend(loc='best', fontsize=9, framealpha=0.9)
ax.grid(True, alpha=0.2)

# Panel 4: Recovery comparison
ax = axes[1, 1]
ax.set_facecolor('#161b22')
for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.tick_params(colors='#c9d1d9')

# Normalize both to peak
v_hh_norm = (V_hh - V_hh[900]) / (np.max(V_hh[1000:2500]) - V_hh[900])
v_liquid_norm = v_liquid / np.max(v_liquid[1000:2500])

t_recover = range(1500, 3500)
ax.plot(t_plot[t_recover], v_hh_norm[t_recover], label='HH Recovery', linewidth=2.5, color='#79c0ff')
ax.plot(t_plot[t_recover], v_liquid_norm[t_recover], label='Liquid Recovery', linewidth=2.5, color='#ff7b72', linestyle='--')
ax.axhline(y=0.5, color='#30363d', linestyle='--', linewidth=1, alpha=0.5, label='50% threshold')

ax.set_xlabel('Time (µs)', color='#c9d1d9', fontsize=11)
ax.set_ylabel('Normalized Signal', color='#c9d1d9', fontsize=11)
ax.set_title('Recovery Dynamics (Normalized)', color='#c9d1d9', fontsize=12, fontweight='bold')
ax.set_ylim(-0.1, 1.2)
ax.legend(loc='best', fontsize=9, framealpha=0.9)
ax.grid(True, alpha=0.2)

plt.tight_layout()
plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim07_biological_comparison.png',
            dpi=150, bbox_inches='tight', facecolor='#0d1117')
print("\n✓ Figure saved: sim07_biological_comparison.png")
plt.close()

print("\n" + "=" * 60)
