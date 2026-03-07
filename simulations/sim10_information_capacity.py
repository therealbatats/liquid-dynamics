"""
SIM10: Information Capacity & Landauer Limit
Shannon capacity and energy efficiency analysis across domain scales.
Author: Ali Ahmed
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# Physical constants
T = 310.15  # K
c0 = 150.0  # mol/m³
D = 1.65e-9  # Average diffusion coefficient (m²/s)
k_B = 1.381e-23
N_A = 6.022e23
lambda_D = 0.78e-9

# Theme
bg = '#0d1117'
axes_color = '#161b22'
spine_color = '#30363d'
text_color = '#c9d1d9'

print("SIM10: Information Capacity & Landauer Limit Analysis")
print(f"Temperature: T = {T} K")
print(f"Baseline concentration: c0 = {c0} mol/m³")
print(f"Diffusion coefficient: D = {D*1e9:.2f}e-9 m²/s")

# Sweep domain size
L_min = 10e-9  # 10 nm
L_max = 10e-6  # 10 μm
n_sweep = 50
L_values = np.logspace(np.log10(L_min), np.log10(L_max), n_sweep)

results = {
    'L': [],
    'C_space': [],
    'bit_rate': [],
    'E_per_bit': [],
    'dx': [],
    'delta_c': [],
    'n_levels': [],
    'n_positions': []
}

print(f"\nSweeping domain size from {L_min*1e9:.1f}nm to {L_max*1e6:.2f}μm...")

for L in L_values:
    Nx = 200
    dx = L / Nx

    # Thermal noise: δc = sqrt(c0 / (N_A * (dx)³))
    volume = dx**3
    delta_c = np.sqrt(c0 / (N_A * volume))

    # Readout timescale
    tau_readout = L**2 / D

    # Spatial resolution: minimum distance resolvable
    # Limited by diffusion spreading and debye screening
    delta_x_diffusion = np.sqrt(2 * D * tau_readout)
    delta_x_min = max(lambda_D, delta_x_diffusion)

    # Signal range: 5*c0 (from c0 to 6*c0)
    signal_range = 5 * c0

    # Number of distinguishable levels
    n_levels = max(signal_range / delta_c, 1)

    # Number of resolvable spatial positions
    n_positions = int(L / delta_x_min)

    # Spatial information capacity
    C_space = n_positions * np.log2(max(n_levels, 1))

    # Temporal bandwidth
    f_max = D / (L**2)

    # Bit rate
    bit_rate = C_space * f_max

    # Energy per bit (Landauer-inspired)
    E_per_bit = k_B * T * (signal_range / c0)**2 / max(C_space, 1)

    results['L'].append(L)
    results['C_space'].append(C_space)
    results['bit_rate'].append(bit_rate)
    results['E_per_bit'].append(E_per_bit)
    results['dx'].append(dx)
    results['delta_c'].append(delta_c)
    results['n_levels'].append(n_levels)
    results['n_positions'].append(n_positions)

# Convert to arrays
for key in results:
    results[key] = np.array(results[key])

# Find optimal L (maximum bit rate)
idx_opt = np.argmax(results['bit_rate'])
L_opt = results['L'][idx_opt]
bit_rate_opt = results['bit_rate'][idx_opt]

print(f"\nOptimal domain size: L = {L_opt*1e9:.1f}nm ({L_opt*1e6:.2f}μm)")
print(f"Maximum bit rate: {bit_rate_opt:.2e} bits/s")
print(f"Spatial capacity at L_opt: {results['C_space'][idx_opt]:.1f} bits")

# Landauer limit at this temperature
E_Landauer = k_B * T * np.log(2)

print(f"Landauer limit: {E_Landauer:.2e} J/bit = {E_Landauer*1e21:.2f} zJ/bit")

# Create 4-panel figure
fig = plt.figure(figsize=(14, 10))
fig.patch.set_facecolor(bg)
gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

# Panel 1: Capacity vs L
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(axes_color)
ax1.loglog(results['L']*1e9, results['C_space'], 'o-', color='#a8e6cf',
           markersize=5, linewidth=2, markeredgecolor=spine_color, markeredgewidth=1)
ax1.axvline(x=L_opt*1e9, color='#ffd93d', linestyle='--', linewidth=2, alpha=0.7, label=f'Optimal: {L_opt*1e9:.1f}nm')
ax1.set_xlabel('Domain Size (nm)', color=text_color, fontsize=11)
ax1.set_ylabel('Spatial Capacity (bits)', color=text_color, fontsize=11)
ax1.set_title('Information Capacity vs Domain Size', color=text_color, fontsize=12, fontweight='bold')
ax1.legend(loc='best', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color)
ax1.tick_params(colors=text_color)
for spine in ax1.spines.values():
    spine.set_color(spine_color)
ax1.grid(True, alpha=0.2, which='both', color=spine_color)

# Panel 2: Bit rate vs L (show peak)
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(axes_color)
ax2.loglog(results['L']*1e9, results['bit_rate'], 's-', color='#ff6b6b',
           markersize=5, linewidth=2, markeredgecolor=spine_color, markeredgewidth=1)
ax2.axvline(x=L_opt*1e9, color='#ffd93d', linestyle='--', linewidth=2, alpha=0.7)
ax2.scatter([L_opt*1e9], [bit_rate_opt], color='#ffd93d', s=200, zorder=5, edgecolor=spine_color, linewidth=2)
ax2.set_xlabel('Domain Size (nm)', color=text_color, fontsize=11)
ax2.set_ylabel('Bit Rate (bits/s)', color=text_color, fontsize=11)
ax2.set_title('Bit Rate: Peak at Optimal L', color=text_color, fontsize=12, fontweight='bold')
ax2.tick_params(colors=text_color)
for spine in ax2.spines.values():
    spine.set_color(spine_color)
ax2.grid(True, alpha=0.2, which='both', color=spine_color)

# Panel 3: Energy per bit vs L (show Landauer)
ax3 = fig.add_subplot(gs[1, 0])
ax3.set_facecolor(axes_color)
ax3.loglog(results['L']*1e9, results['E_per_bit']*1e21, '^-', color='#4ecdc4',
           markersize=5, linewidth=2, markeredgecolor=spine_color, markeredgewidth=1, label='Liquid ion system')
ax3.axhline(y=E_Landauer*1e21, color='#ff6b6b', linestyle='--', linewidth=2.5, alpha=0.8, label='Landauer limit')
ax3.set_xlabel('Domain Size (nm)', color=text_color, fontsize=11)
ax3.set_ylabel('Energy per Bit (zJ)', color=text_color, fontsize=11)
ax3.set_title('Energy Efficiency vs Domain Size', color=text_color, fontsize=12, fontweight='bold')
ax3.legend(loc='best', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color)
ax3.tick_params(colors=text_color)
for spine in ax3.spines.values():
    spine.set_color(spine_color)
ax3.grid(True, alpha=0.2, which='both', color=spine_color)

# Panel 4: Comparison bar (liquid vs SRAM vs neuron)
ax4 = fig.add_subplot(gs[1, 1])
ax4.set_facecolor(axes_color)

# Representative energies at optimal L
E_liquid = results['E_per_bit'][idx_opt] * 1e21  # zJ
E_sram = 1.0  # fJ = 1000 zJ
E_neuron = 10.0 * 1000  # 10 fJ = 10000 zJ

systems = ['Liquid Ion\n(This work)', 'SRAM', 'Biological\nNeuron']
energies = [E_liquid, E_sram, E_neuron]
colors_bar = ['#a8e6cf', '#ffd93d', '#ff6b6b']

bars = ax4.bar(systems, energies, color=colors_bar, alpha=0.8, edgecolor=spine_color, linewidth=1.5)
ax4.axhline(y=E_Landauer*1e21, color='#00ff00', linestyle='--', linewidth=2, alpha=0.6, label='Landauer limit')
ax4.set_ylabel('Energy per Bit (zJ)', color=text_color, fontsize=11)
ax4.set_title('Technology Comparison', color=text_color, fontsize=12, fontweight='bold')
ax4.set_yscale('log')
ax4.legend(loc='upper left', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color)
ax4.tick_params(colors=text_color)
for spine in ax4.spines.values():
    spine.set_color(spine_color)
ax4.grid(True, alpha=0.2, axis='y', which='both', color=spine_color)

# Add value labels
for bar, val in zip(bars, energies):
    height = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2., height*1.2, f'{val:.0f}zJ',
             ha='center', va='bottom', color=text_color, fontsize=10, fontweight='bold')

plt.suptitle('SIM10: Information Capacity & Landauer Limit Analysis',
             fontsize=14, fontweight='bold', color=text_color, y=0.995)

plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim10_information_capacity.png',
            dpi=150, bbox_inches='tight', facecolor=bg)
print("\nFigure saved: sim10_information_capacity.png")
plt.close()

print("\n=== SIM10 COMPLETE ===")
