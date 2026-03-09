#!/usr/bin/env python3
"""
Simulation 18: Noise Analysis and SNR Limits
Comprehensive study of thermal noise, shot noise, and measurement noise
in liquid computing and their effects on signal detection.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Physical Parameters
# ============================================================================

T = 310.15          # Temperature (K), body temperature
c0 = 150.0          # Reference concentration (mol/m^3)
D = 1.96e-9         # Diffusion coefficient (m^2/s)
F = 96485.0         # Faraday constant (C/mol)
R = 8.314           # Gas constant (J/(mol·K))
VT = R * T / F      # Thermal voltage (~26.7 mV at body temp)

# Spatial parameters
N = 80              # Number of grid points
L = 50e-9           # Domain length (m)
dx = L / N          # Spatial step
dt = 0.3 * dx**2 / (2 * D)  # Time step (stability)

# Physical constants
kB = 1.38064852e-23  # Boltzmann constant (J/K)
e_charge = 1.602e-19  # Elementary charge (C)
Avogadro = 6.022e23  # Avogadro's number

# Simulation parameters
n_noise_realizations = 50  # Monte Carlo runs
n_steps = 300          # Time steps for signal detection
n_sweeps = 10          # Domain size sweep points

# ============================================================================
# Noise Model Calculations
# ============================================================================

# Thermal (Johnson-Nyquist) noise on ionic concentrations
# From equipartition: kB*T = (1/2)*m*v^2 applied to concentration fluctuations
sigma_thermal = np.sqrt(kB * T / (F**2 * dx * c0 / (Avogadro * 1000)))

# Shot noise from finite ion count (Poisson statistics)
N_ions = c0 * (dx**3) * Avogadro / 1000  # Number of ions in a voxel
sigma_shot = c0 / np.sqrt(N_ions)

# Total noise (assuming thermal and shot are independent)
sigma_total = np.sqrt(sigma_thermal**2 + sigma_shot**2)

# ============================================================================
# 1. Signal Model and SNR Analysis
# ============================================================================

# Signal amplitude sweep (logarithmically spaced)
A_sig_values = np.logspace(np.log10(0.001 * c0), np.log10(2.0 * c0), 20)

# Compute SNR for each amplitude
SNR_linear = A_sig_values / sigma_total
SNR_dB = 20 * np.log10(SNR_linear)

# Minimum detectable signal (MDS): SNR = 1 (0 dB)
idx_mds = np.argmax(SNR_dB >= 0)
mds = A_sig_values[idx_mds]
snr_at_mds = SNR_linear[idx_mds]

# SNR at specific amplitudes
snr_01 = 20 * np.log10(0.1 * c0 / sigma_total)
snr_10 = 20 * np.log10(1.0 * c0 / sigma_total)

# ============================================================================
# 2. Monte Carlo Noise Realization Study
# ============================================================================

# Selected amplitude values for detailed analysis
A_mc_values = np.array([0.01, 0.05, 0.1, 0.5, 1.0]) * c0

# Storage for Monte Carlo results
mc_results = {
    'A_sig': A_mc_values,
    'mean_signal': np.zeros_like(A_mc_values),
    'std_signal': np.zeros_like(A_mc_values),
    'detection_prob': np.zeros_like(A_mc_values),
}

omega = np.pi / (60 * dt)  # Angular frequency for sinusoidal perturbation

print("Running Monte Carlo noise realizations...")
for i, A in enumerate(A_mc_values):
    signal_estimates = []
    detected = 0

    for realization in range(n_noise_realizations):
        # Initialize concentration field
        c = np.ones(N) * c0

        # Time integration with noise
        c_time_series = []

        for step in range(n_steps):
            t = step * dt

            # Apply sinusoidal left BC with noise
            noise = np.random.normal(0, sigma_total, N)
            c = c + noise

            # Simple forward Euler diffusion step
            c_new = c.copy()
            for j in range(1, N-1):
                c_new[j] = c[j] + dt/dx**2 * D * (c[j+1] - 2*c[j] + c[j-1])

            # Left boundary: sinusoidal source + noise
            c_new[0] = c0 + A * np.sin(omega * t) + np.random.normal(0, sigma_total)
            # Right boundary: no-flux (symmetric)
            c_new[-1] = c_new[-2]

            c = c_new
            c_time_series.append(np.mean(c))

        # Estimate signal as std of mean concentration over time
        c_ts = np.array(c_time_series)
        signal_est = np.std(c_ts)
        signal_estimates.append(signal_est)

        # Detection criterion: estimated signal > 2 * noise floor
        if signal_est > 2 * sigma_total:
            detected += 1

    mc_results['mean_signal'][i] = np.mean(signal_estimates)
    mc_results['std_signal'][i] = np.std(signal_estimates)
    mc_results['detection_prob'][i] = detected / n_noise_realizations

# ============================================================================
# 3. Optimal Domain Size Analysis
# ============================================================================

L_sweep = np.logspace(np.log10(5e-9), np.log10(500e-9), n_sweeps)  # 5nm to 500nm
SNR_vs_L = np.zeros_like(L_sweep)
sigma_thermal_vs_L = np.zeros_like(L_sweep)
sigma_shot_vs_L = np.zeros_like(L_sweep)

for i, L_i in enumerate(L_sweep):
    dx_i = L_i / N

    # Thermal noise (inversely proportional to sqrt(dx))
    sigma_th = np.sqrt(kB * T / (F**2 * dx_i * c0 / (Avogadro * 1000)))

    # Shot noise (independent of dx)
    N_ions_i = c0 * (dx_i**3) * Avogadro / 1000
    sigma_sh = c0 / np.sqrt(N_ions_i)

    sigma_total_i = np.sqrt(sigma_th**2 + sigma_sh**2)

    # SNR at A = 0.5 * c0
    SNR_vs_L[i] = 20 * np.log10(0.5 * c0 / sigma_total_i)
    sigma_thermal_vs_L[i] = sigma_th
    sigma_shot_vs_L[i] = sigma_sh

# Find optimal L
idx_optimal = np.argmax(SNR_vs_L)
L_opt = L_sweep[idx_optimal]
SNR_max = SNR_vs_L[idx_optimal]

# ============================================================================
# 4. Noise Floor Energy
# ============================================================================

E_noise = kB * T * np.log(2) * (1 + sigma_total / c0)**2

# ============================================================================
# Print Results
# ============================================================================

print(f"Thermal noise sigma: {sigma_thermal:.4e} mol/m^3")
print(f"Shot noise sigma: {sigma_shot:.4e} mol/m^3")
print(f"Total noise sigma: {sigma_total:.4e} mol/m^3")
print(f"Min detectable signal: {mds/c0:.4f} x c0")
print(f"SNR at A=0.1*c0: {snr_01:.2f} dB")
print(f"SNR at A=1.0*c0: {snr_10:.2f} dB")
print(f"Optimal domain size for SNR: {L_opt*1e9:.1f} nm")
print(f"Noise floor energy/bit: {E_noise:.3e} J")

# ============================================================================
# Plotting
# ============================================================================

# Set dark theme
plt.style.use('dark_background')
rcParams.update({
    'figure.facecolor': '#0d1117',
    'axes.facecolor': '#161b22',
    'axes.edgecolor': '#c9d1d9',
    'text.color': '#c9d1d9',
    'xtick.color': '#c9d1d9',
    'ytick.color': '#c9d1d9',
    'grid.color': '#30363d',
    'font.size': 11,
})

fig = plt.figure(figsize=(14, 10), dpi=150)
fig.patch.set_facecolor('#0d1117')

# Panel 1: SNR vs Signal Amplitude (log-log)
ax1 = plt.subplot(3, 2, 1)
ax1.set_facecolor('#161b22')
ax1.loglog(A_sig_values / c0, SNR_linear, 'o-', color='#58a6ff', linewidth=2, markersize=4, label='SNR')

# Noise floors
ax1.axhline(sigma_thermal / (0.5 * c0), color='#3fb950', linestyle='--', linewidth=1.5, label='Thermal floor')
ax1.axhline(sigma_shot / (0.5 * c0), color='#fb8500', linestyle='--', linewidth=1.5, label='Shot floor')
ax1.axhline(sigma_total / (0.5 * c0), color='#ffffff', linestyle='--', linewidth=1.5, alpha=0.7, label='Total floor')
ax1.axhline(1.0, color='#d1d5da', linestyle=':', linewidth=1, alpha=0.5, label='SNR=1 (0dB)')

# Mark MDS
ax1.plot(mds / c0, 1.0, 'r*', markersize=20, label='MDS')

ax1.set_xlabel('Signal amplitude (x c0)', color='#c9d1d9')
ax1.set_ylabel('SNR (linear)', color='#c9d1d9')
ax1.set_title('Panel 1: SNR vs Signal Amplitude', color='#c9d1d9', fontsize=12, fontweight='bold')
ax1.legend(fontsize=9, loc='lower right')
ax1.grid(True, alpha=0.2)

# Panel 2: Noise Contributions vs Domain Length
ax2 = plt.subplot(3, 2, 2)
ax2.set_facecolor('#161b22')
ax2.loglog(L_sweep * 1e9, sigma_thermal_vs_L / c0, 'o-', color='#3fb950', linewidth=2, markersize=5, label='Thermal')
ax2.loglog(L_sweep * 1e9, sigma_shot_vs_L / c0, 's-', color='#fb8500', linewidth=2, markersize=5, label='Shot')
ax2.loglog(L_sweep * 1e9, np.sqrt(sigma_thermal_vs_L**2 + sigma_shot_vs_L**2) / c0, '^-',
           color='#ffffff', linewidth=2, markersize=5, alpha=0.7, label='Total')

# Mark crossover
crossover_idx = np.argmin(np.abs(sigma_thermal_vs_L - sigma_shot_vs_L))
ax2.plot(L_sweep[crossover_idx] * 1e9, sigma_thermal_vs_L[crossover_idx] / c0, 'r*', markersize=20, label='Crossover')

ax2.set_xlabel('Domain length (nm)', color='#c9d1d9')
ax2.set_ylabel('Noise std (x c0)', color='#c9d1d9')
ax2.set_title('Panel 2: Noise Sources vs Domain Size', color='#c9d1d9', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9, loc='best')
ax2.grid(True, alpha=0.2)

# Panel 3: Monte Carlo Detection Probability
ax3 = plt.subplot(3, 2, 3)
ax3.set_facecolor('#161b22')
ax3.semilogx(A_mc_values / c0, mc_results['detection_prob'], 'o-', color='#58a6ff',
             linewidth=2, markersize=8, label='Detection prob')
ax3.fill_between(A_mc_values / c0,
                  mc_results['detection_prob'] - 0.1,
                  mc_results['detection_prob'] + 0.1,
                  alpha=0.2, color='#58a6ff')
ax3.axhline(0.5, color='#d1d5da', linestyle=':', linewidth=1, alpha=0.5)
ax3.set_xlabel('Signal amplitude (x c0)', color='#c9d1d9')
ax3.set_ylabel('Detection probability', color='#c9d1d9')
ax3.set_title('Panel 3: Monte Carlo Detection (50 realizations)', color='#c9d1d9', fontsize=12, fontweight='bold')
ax3.set_ylim([-0.05, 1.05])
ax3.grid(True, alpha=0.2)
ax3.legend(fontsize=9)

# Panel 4: SNR vs Domain Size
ax4 = plt.subplot(3, 2, 4)
ax4.set_facecolor('#161b22')
ax4.semilogx(L_sweep * 1e9, SNR_vs_L, 'o-', color='#58a6ff', linewidth=2, markersize=6)
ax4.plot(L_opt * 1e9, SNR_max, 'r*', markersize=20, label=f'Optimal L={L_opt*1e9:.1f} nm')
ax4.axhline(0, color='#d1d5da', linestyle=':', linewidth=1, alpha=0.5)
ax4.set_xlabel('Domain length (nm)', color='#c9d1d9')
ax4.set_ylabel('SNR (dB) at A=0.5*c0', color='#c9d1d9')
ax4.set_title('Panel 4: SNR Optimization vs Domain Size', color='#c9d1d9', fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.2)
ax4.legend(fontsize=9)

# Panel 5: Time Series Comparison (bottom, full width)
ax5 = plt.subplot(3, 1, 3)
ax5.set_facecolor('#161b22')

# Generate time series for three amplitude values
amplitudes_ts = [0.01, 0.1, 1.0]
colors_ts = ['#3fb950', '#58a6ff', '#fb8500']
y_offsets = [0, c0, 2*c0]

for amp_idx, (A_ts, color, y_off) in enumerate(zip(amplitudes_ts, colors_ts, y_offsets)):
    # Generate clean signal
    t_array = np.arange(n_steps) * dt
    signal_clean = np.sin(omega * t_array) * A_ts

    # Add noise realization
    noise_ts = np.random.normal(0, sigma_total, n_steps)
    signal_noisy = signal_clean + noise_ts

    # Plot
    ax5.plot(t_array * 1e9, signal_noisy + y_off, color=color, linewidth=1.5, alpha=0.8,
             label=f'A={A_ts*c0:.3f} mol/m³')
    ax5.plot(t_array * 1e9, signal_clean + y_off, color=color, linewidth=2.5, alpha=0.3, linestyle='--')

ax5.set_xlabel('Time (ns)', color='#c9d1d9')
ax5.set_ylabel('Signal + Noise offset', color='#c9d1d9')
ax5.set_title('Panel 5: Time Series Evolution Across Signal Amplitudes', color='#c9d1d9', fontsize=12, fontweight='bold')
ax5.legend(fontsize=10, loc='upper right', ncol=3)
ax5.grid(True, alpha=0.2)

plt.tight_layout()
plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim18_noise_analysis.png',
            dpi=150, facecolor='#0d1117', edgecolor='none')
print("\nFigure saved to: /sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim18_noise_analysis.png")

plt.close()

print("\nSimulation 18 completed successfully!")
