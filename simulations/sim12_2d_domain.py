"""
SIM12: 2D Domain Symmetry-Based Computation
Extend to 2D (50nm × 50nm, 80×80 grid) with symmetric/asymmetric sources.
Analyzes spatial entropy enhancement in 2D vs 1D.
Author: Ali Ahmed
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.ndimage import convolve
import warnings
warnings.filterwarnings('ignore')

# Physical constants
T = 310.15
c0 = 150.0
D = 1.65e-9  # m²/s
k_B = 1.381e-23
N_A = 6.022e23

# Domain
L_2d = 50e-9  # 50 nm × 50 nm
Nx_2d = 80
Ny_2d = 80
dx = L_2d / Nx_2d
dy = L_2d / Ny_2d
x_2d = np.linspace(0, L_2d, Nx_2d)
y_2d = np.linspace(0, L_2d, Ny_2d)

# Time stepping (explicit with stability constraint)
dt = 0.4 * min(dx, dy)**2 / (4 * D)
tau_diff = L_2d**2 / D
t_end = 2.0 * tau_diff
Nt = int(t_end / dt)

print("SIM12: 2D Domain Analysis with Symmetry")
print(f"Domain: L = {L_2d*1e9:.1f}nm × {L_2d*1e9:.1f}nm")
print(f"Grid: {Nx_2d} × {Ny_2d} = {Nx_2d*Ny_2d} cells")
print(f"Grid spacing: dx = dy = {dx*1e9:.3f}nm")
print(f"Time: t_end = {t_end*1e6:.3f}μs ({t_end/tau_diff:.2f}τ_diff), Nt = {Nt}")
print(f"Timestep: dt = {dt*1e9:.3f}ns, Stability: {D*dt/(dx**2):.4f} < 0.25")

# Theme
bg = '#0d1117'
axes_color = '#161b22'
spine_color = '#30363d'
text_color = '#c9d1d9'

def laplacian_2d(c, dx, dy):
    """Compute 2D Laplacian with zero-flux boundary conditions."""
    kernel = np.array([[0, 1, 0],
                       [1, -4, 1],
                       [0, 1, 0]]) / (dx*dy)
    lapl = convolve(c, kernel, mode='constant', cval=0)
    # Zero-flux boundaries
    lapl[0, :] = 0
    lapl[-1, :] = 0
    lapl[:, 0] = 0
    lapl[:, -1] = 0
    return lapl

def step_diffusion_2d(c, D, dt, dx, dy):
    """Step diffusion: dc/dt = D*∇²c"""
    lapl = laplacian_2d(c, dx, dy)
    c_new = c + D * dt * lapl
    # Clip to stable range
    c_new = np.clip(c_new, 0.01*c0, 20*c0)
    return c_new

def compute_entropy_2d(c):
    """Compute spatial entropy of 2D field."""
    c_flat = c.flatten()
    c_sum = np.sum(c_flat)
    if c_sum <= 0:
        return 0
    p = c_flat / c_sum
    p = p[p > 1e-10]
    H = -np.sum(p * np.log2(p))
    return H

def compute_entropy_1d(c_1d):
    """Compute spatial entropy of 1D field."""
    c_sum = np.sum(c_1d)
    if c_sum <= 0:
        return 0
    p = c_1d / c_sum
    p = p[p > 1e-10]
    H = -np.sum(p * np.log2(p))
    return H

def compute_symmetry_measure(c_2d):
    """Compute measure of asymmetry: how much does center row differ from average."""
    center_row = c_2d[c_2d.shape[0]//2, :]
    row_entropy = compute_entropy_1d(center_row)
    field_entropy = compute_entropy_2d(c_2d)
    return field_entropy / max(row_entropy, 1)

# Define scenarios
scenarios = {
    'single_source': {
        'name': 'Single Source (Corner)',
        'init': lambda c: c,
        'color': '#ff6b6b'
    },
    'symmetric_two': {
        'name': 'Symmetric Two Sources (Diagonal)',
        'init': lambda c: c,
        'color': '#a8e6cf'
    },
    'asymmetric_two': {
        'name': 'Asymmetric Two Sources',
        'init': lambda c: c,
        'color': '#4ecdc4'
    }
}

# Results storage
results = {
    'single_source': {},
    'symmetric_two': {},
    'asymmetric_two': {}
}

print("\n" + "="*60)
print("Running 2D simulations...")
print("="*60)

for scenario_key, scenario_info in scenarios.items():
    print(f"\n{scenario_info['name']}:")

    # Initialize concentration
    c = np.ones((Nx_2d, Ny_2d)) * c0

    # Set source conditions
    if scenario_key == 'single_source':
        # Injection at corner (20% from edge)
        i0 = int(0.2 * Nx_2d)
        j0 = int(0.2 * Ny_2d)
        c[i0, j0] = 5 * c0

    elif scenario_key == 'symmetric_two':
        # Two diagonal corners
        i0 = int(0.2 * Nx_2d)
        j0 = int(0.2 * Ny_2d)
        i1 = Nx_2d - i0
        j1 = Ny_2d - j0
        c[i0, j0] = 5 * c0
        c[i1, j1] = 5 * c0

    elif scenario_key == 'asymmetric_two':
        # One corner + one edge midpoint
        i0 = int(0.2 * Nx_2d)
        j0 = int(0.2 * Ny_2d)
        i_mid = Nx_2d // 2
        j_edge = 5
        c[i0, j0] = 5 * c0
        c[i_mid, j_edge] = 5 * c0

    # Time integration
    entropy_2d_history = []
    entropy_1d_history = []
    symmetry_history = []
    times = np.linspace(0, t_end, 50)
    time_idx = 0
    c_snapshots = {}

    for step in range(Nt):
        t = step * dt

        # Store snapshots at key times
        for key_time in [0.5*tau_diff, tau_diff, 2*tau_diff]:
            if abs(t - key_time) < dt*2 and key_time not in c_snapshots:
                c_snapshots[key_time] = c.copy()

        # Update
        c = step_diffusion_2d(c, D, dt, dx, dy)

        # Sample entropy
        if time_idx < len(times) and t >= times[time_idx]:
            H_2d = compute_entropy_2d(c)
            center_row = c[c.shape[0]//2, :]
            H_1d = compute_entropy_1d(center_row)
            sym_measure = compute_symmetry_measure(c)

            entropy_2d_history.append(H_2d)
            entropy_1d_history.append(H_1d)
            symmetry_history.append(sym_measure)
            time_idx += 1

    results[scenario_key]['entropy_2d'] = np.array(entropy_2d_history)
    results[scenario_key]['entropy_1d'] = np.array(entropy_1d_history)
    results[scenario_key]['symmetry'] = np.array(symmetry_history)
    results[scenario_key]['c_final'] = c
    results[scenario_key]['c_snapshots'] = c_snapshots
    results[scenario_key]['times'] = np.linspace(0, t_end, len(entropy_2d_history))

    # Compute enhancement factor
    enhancement = np.mean(results[scenario_key]['entropy_2d']) / np.mean(results[scenario_key]['entropy_1d'])
    print(f"  2D entropy: {np.mean(results[scenario_key]['entropy_2d']):.3f} bits")
    print(f"  1D entropy: {np.mean(results[scenario_key]['entropy_1d']):.3f} bits")
    print(f"  Enhancement: {enhancement:.2f}×")

# Create 6-panel figure (3×2)
fig = plt.figure(figsize=(16, 12))
fig.patch.set_facecolor(bg)
gs = GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.3)

scenario_keys = ['single_source', 'symmetric_two', 'asymmetric_two']

for row, scenario_key in enumerate(scenario_keys):
    scenario_info = scenarios[scenario_key]

    # Left panel: 2D heatmap
    ax_heat = fig.add_subplot(gs[row, 0])
    ax_heat.set_facecolor(axes_color)

    c_final = results[scenario_key]['c_final']
    im = ax_heat.contourf(x_2d*1e9, y_2d*1e9, c_final.T/c0, levels=20, cmap='inferno')

    ax_heat.set_xlabel('X (nm)', color=text_color, fontsize=10)
    ax_heat.set_ylabel('Y (nm)', color=text_color, fontsize=10)
    ax_heat.set_title(f'{scenario_info["name"]}: Final State', color=text_color, fontsize=11, fontweight='bold')
    ax_heat.set_aspect('equal')
    ax_heat.tick_params(colors=text_color)
    for spine in ax_heat.spines.values():
        spine.set_color(spine_color)

    cbar = plt.colorbar(im, ax=ax_heat)
    cbar.set_label('Concentration (c₀)', color=text_color, fontsize=9)
    cbar.ax.tick_params(colors=text_color)

    # Right panel: Time evolution curves
    ax_evo = fig.add_subplot(gs[row, 1])
    ax_evo.set_facecolor(axes_color)

    times = results[scenario_key]['times']
    entropy_2d = results[scenario_key]['entropy_2d']
    entropy_1d = results[scenario_key]['entropy_1d']

    ax_evo.plot(times/tau_diff, entropy_2d, 'o-', color=scenario_info['color'],
                markersize=4, linewidth=2, label='2D Field Entropy', alpha=0.8)
    ax_evo.plot(times/tau_diff, entropy_1d, 's--', color='#ffd93d',
                markersize=4, linewidth=2, label='1D Center Row Entropy', alpha=0.8)

    ax_evo.set_xlabel('Time (τ_diff)', color=text_color, fontsize=10)
    ax_evo.set_ylabel('Shannon Entropy (bits)', color=text_color, fontsize=10)
    ax_evo.set_title(f'{scenario_info["name"]}: Entropy Evolution', color=text_color, fontsize=11, fontweight='bold')
    ax_evo.legend(loc='best', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color, fontsize=9)
    ax_evo.tick_params(colors=text_color)
    for spine in ax_evo.spines.values():
        spine.set_color(spine_color)
    ax_evo.grid(True, alpha=0.2, color=spine_color)

# Create additional comparison figure (3 panels)
fig2 = plt.figure(figsize=(16, 5))
fig2.patch.set_facecolor(bg)
gs2 = GridSpec(1, 3, figure=fig2, hspace=0.3, wspace=0.35)

# Panel 1: Entropy comparison heatmap
ax_comp = fig2.add_subplot(gs2[0, 0])
ax_comp.set_facecolor(axes_color)

entropy_data = np.array([
    np.mean(results[sk]['entropy_2d']) for sk in scenario_keys
] + [
    np.mean(results[sk]['entropy_1d']) for sk in scenario_keys
]).reshape(2, 3)

im_comp = ax_comp.imshow(entropy_data, cmap='viridis', aspect='auto')
ax_comp.set_xticks(range(3))
ax_comp.set_xticklabels(['Single', 'Symmetric', 'Asymmetric'], color=text_color)
ax_comp.set_yticks(range(2))
ax_comp.set_yticklabels(['2D Field', '1D Row'], color=text_color)
ax_comp.set_title('Entropy Comparison Matrix', color=text_color, fontsize=12, fontweight='bold')

# Add text annotations
for i in range(2):
    for j in range(3):
        text = ax_comp.text(j, i, f'{entropy_data[i, j]:.1f}',
                           ha="center", va="center", color=text_color, fontweight='bold')

cbar2 = plt.colorbar(im_comp, ax=ax_comp)
cbar2.set_label('Entropy (bits)', color=text_color, fontsize=10)
cbar2.ax.tick_params(colors=text_color)

# Panel 2: Enhancement factor bar chart
ax_enhance = fig2.add_subplot(gs2[0, 1])
ax_enhance.set_facecolor(axes_color)

enhancements = [
    np.mean(results[sk]['entropy_2d']) / np.mean(results[sk]['entropy_1d'])
    for sk in scenario_keys
]
colors_enhance = [scenarios[sk]['color'] for sk in scenario_keys]
labels_enhance = ['Single', 'Symmetric', 'Asymmetric']

bars = ax_enhance.bar(labels_enhance, enhancements, color=colors_enhance, alpha=0.8,
                      edgecolor=spine_color, linewidth=1.5)
ax_enhance.axhline(y=1.74, color='#45b7d1', linestyle='--', linewidth=2, alpha=0.7, label='Expected ~1.74×')
ax_enhance.set_ylabel('2D/1D Entropy Ratio', color=text_color, fontsize=11)
ax_enhance.set_title('Dimensionality Enhancement', color=text_color, fontsize=12, fontweight='bold')
ax_enhance.legend(loc='upper left', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color)
ax_enhance.tick_params(colors=text_color)
for spine in ax_enhance.spines.values():
    spine.set_color(spine_color)
ax_enhance.grid(True, alpha=0.2, axis='y', color=spine_color)

# Add value labels
for bar, val in zip(bars, enhancements):
    height = bar.get_height()
    ax_enhance.text(bar.get_x() + bar.get_width()/2., height, f'{val:.2f}×',
                   ha='center', va='bottom', color=text_color, fontsize=10, fontweight='bold')

# Panel 3: Symmetry measure over time
ax_sym = fig2.add_subplot(gs2[0, 2])
ax_sym.set_facecolor(axes_color)

for scenario_key in scenario_keys:
    times = results[scenario_key]['times']
    symmetry = results[scenario_key]['symmetry']
    ax_sym.plot(times/tau_diff, symmetry, 'o-', color=scenarios[scenario_key]['color'],
                markersize=4, linewidth=2, label=scenario_key.replace('_', ' ').title(), alpha=0.8)

ax_sym.set_xlabel('Time (τ_diff)', color=text_color, fontsize=11)
ax_sym.set_ylabel('Entropy Ratio (2D/1D)', color=text_color, fontsize=11)
ax_sym.set_title('Symmetry Measure Evolution', color=text_color, fontsize=12, fontweight='bold')
ax_sym.legend(loc='best', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color, fontsize=9)
ax_sym.tick_params(colors=text_color)
for spine in ax_sym.spines.values():
    spine.set_color(spine_color)
ax_sym.grid(True, alpha=0.2, color=spine_color)

plt.suptitle('SIM12: 2D Domain Symmetry Analysis',
             fontsize=14, fontweight='bold', color=text_color, y=0.995)

plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim12_2d_domain.png',
            dpi=150, bbox_inches='tight', facecolor=bg)
print("\nFigure saved: sim12_2d_domain.png")
plt.close()

# Close first figure if still open
plt.close('all')

print("\n=== SIM12 COMPLETE ===")
