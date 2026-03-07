#!/usr/bin/env python3
"""
Simulation 13: 3D Spherical Droplet Geometry
Comparing 1D slab, 2D disk, and 3D spherical geometries for information storage
capacity and entropy in liquid ionic systems.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
from matplotlib.colors import LogNorm

# Physical parameters (exactly as specified)
T = 310.15  # K
c0 = 150.0  # mol/m³
D = 1.96e-9  # m²/s (K+ diffusivity)
F = 96485.0  # Faraday constant
R = 8.314   # Gas constant
VT = R * T / F  # Thermal voltage = 0.02669 V
lambda_D = 0.78e-9  # Debye length (m)
N = 60  # grid points per dimension
L = 50e-9  # domain size (m)

print(f"Physical parameters:")
print(f"T = {T} K")
print(f"c0 = {c0} mol/m³")
print(f"D = {D} m²/s")
print(f"VT = {VT:.5f} V")
print(f"lambda_D = {lambda_D} m")
print(f"N = {N}, L = {L*1e9} nm")
print(f"Debye parameter L/lambda_D = {L/lambda_D:.1f}")
print()

# Time scaling
t_final = L**2 / (np.pi**2 * D)
print(f"t_final = {t_final:.3e} s")
print()

# ============================================================================
# 1D SLAB GEOMETRY
# ============================================================================
def solve_1d_slab():
    """
    Solve 1D diffusion: dc/dt = D * d²c/dx²
    IC: c = c0 + 2*c0*sin(pi*x/L)
    BC: c = c0 at x=0 and x=L (fixed)
    """
    x = np.linspace(0, L, N)
    dx = x[1] - x[0]
    dt = 0.3 * dx**2 / D  # CFL-stable timestep

    # Initial condition
    c = c0 + 2*c0*np.sin(np.pi*x/L)

    # Time stepping with explicit finite differences
    num_steps = int(np.ceil(t_final / dt))
    actual_dt = t_final / num_steps

    for step in range(num_steps):
        # Interior points: dc/dt = D * (c[i+1] - 2*c[i] + c[i-1]) / dx²
        c_new = c.copy()
        for i in range(1, N-1):
            c_new[i] = c[i] + actual_dt * D * (c[i+1] - 2*c[i] + c[i-1]) / dx**2
        # Boundary conditions (Dirichlet)
        c_new[0] = c0
        c_new[-1] = c0
        c = c_new

    return x, c

x_1d, c_1d = solve_1d_slab()
print(f"1D slab simulation completed")
print(f"1D concentration range: [{c_1d.min():.1f}, {c_1d.max():.1f}] mol/m³")
print()

# ============================================================================
# 2D DISK GEOMETRY (POLAR COORDINATES)
# ============================================================================
def solve_2d_disk():
    """
    Solve 2D diffusion on disk using Cartesian coordinates (x,y) with a radial mask.
    This avoids the 1/r singularity issue of polar coordinates.
    """
    # Use Cartesian grid from -L to L
    x = np.linspace(-L, L, N)
    y = np.linspace(-L, L, N)
    dx = x[1] - x[0]
    dy = y[1] - y[0]

    dt = 0.2 * dx**2 / D  # CFL-stable

    # Create 2D grid
    X, Y = np.meshgrid(x, y, indexing='ij')
    R = np.sqrt(X**2 + Y**2)

    # Initial condition (from polar: cos(theta) = x/r at a given r)
    c = np.zeros_like(R)
    mask = R <= L
    c[mask] = c0 + 2*c0*np.sin(np.pi*R[mask]/L)*np.cos(np.arctan2(Y[mask], X[mask]))

    # Time stepping
    num_steps = int(np.ceil(t_final / dt))
    actual_dt = t_final / num_steps

    for step in range(num_steps):
        c_new = c.copy()

        # Interior points in domain
        for i in range(1, N-1):
            for j in range(1, N-1):
                if R[i, j] <= L:
                    # Standard 2D Laplacian
                    d2c_dx2 = (c[i+1, j] - 2*c[i, j] + c[i-1, j]) / dx**2
                    d2c_dy2 = (c[i, j+1] - 2*c[i, j] + c[i, j-1]) / dy**2
                    laplacian = d2c_dx2 + d2c_dy2

                    c_new[i, j] = c[i, j] + actual_dt * D * laplacian

        # Boundary condition: c = c0 at r = L
        c_new[R > L] = c0
        # Also set region outside domain
        c_new[R > 1.05*L] = c0

        c = c_new

    return x, y, c, R

x_2d, y_2d, c_2d, R_2d = solve_2d_disk()
print(f"2D disk simulation completed")
print(f"2D concentration range: [{c_2d.min():.1f}, {c_2d.max():.1f}] mol/m³")
print()

# ============================================================================
# 3D SPHERE GEOMETRY (RADIAL ONLY)
# ============================================================================
def solve_3d_sphere():
    """
    Solve 3D spherical diffusion (1D radial with spherical symmetry):
    dc/dt = D*(d²c/dr² + 2/r*dc/dr)
    IC: c = c0 + 2*c0*sin(pi*r/L)
    BC: Neumann at r=0 (symmetry), Dirichlet c=c0 at r=L
    """
    r = np.linspace(0, L, N)
    dr = r[1] - r[0]

    dt = 0.3 * dr**2 / (4 * D)  # Similar CFL as 2D

    # Initial condition
    c = c0 + 2*c0*np.sin(np.pi*r/L)

    # Time stepping
    num_steps = int(np.ceil(t_final / dt))
    actual_dt = t_final / num_steps

    for step in range(num_steps):
        c_new = c.copy()

        # Interior points (r > 0)
        for i in range(1, N-1):
            r_i = r[i]
            # Derivatives
            dc_dr = (c[i+1] - c[i-1]) / (2*dr)
            d2c_dr2 = (c[i+1] - 2*c[i] + c[i-1]) / dr**2

            # Spherical Laplacian
            laplacian = d2c_dr2 + (2/r_i)*dc_dr
            c_new[i] = c[i] + actual_dt * D * laplacian

        # Boundary at r=L (Dirichlet)
        c_new[-1] = c0

        # Boundary at r=0 (Neumann: dc/dr = 0)
        # Ghost point method: c_new[0] = c_new[1]
        c_new[0] = c_new[1]

        c = c_new

    return r, c

r_3d, c_3d = solve_3d_sphere()
print(f"3D sphere simulation completed")
print(f"3D concentration range: [{c_3d.min():.1f}, {c_3d.max():.1f}] mol/m³")
print()

# ============================================================================
# ENTROPY ANALYSIS
# ============================================================================
def compute_entropy(c_profile):
    """
    Compute Shannon entropy: H = -sum(p * log2(p))
    where p is the normalized concentration (probability distribution)
    """
    c_pos = np.maximum(c_profile, 1e-10)  # Avoid log(0)
    p = c_pos / np.sum(c_pos)  # Normalize
    H = -np.sum(p * np.log2(p))
    return H

entropy_1d = compute_entropy(c_1d)
entropy_2d = compute_entropy(c_2d.flatten())
entropy_3d = compute_entropy(c_3d)

print(f"Shannon Entropy Analysis:")
print(f"1D entropy: {entropy_1d:.3f} bits")
print(f"2D entropy: {entropy_2d:.3f} bits")
print(f"3D entropy: {entropy_3d:.3f} bits")

ratio_2d = entropy_2d / entropy_1d
ratio_3d = entropy_3d / entropy_1d

print(f"2D/1D ratio: {ratio_2d:.3f}")
print(f"3D/1D ratio: {ratio_3d:.3f}")
print(f"3D/2D ratio: {ratio_3d/ratio_2d:.3f}")
print()

# Spatial complexity (effective independent modes)
complexity_1d = np.exp(entropy_1d)
complexity_2d = np.exp(entropy_2d)
complexity_3d = np.exp(entropy_3d)

print(f"Spatial Complexity (exp(H)):")
print(f"1D: {complexity_1d:.2f}")
print(f"2D: {complexity_2d:.2f}")
print(f"3D: {complexity_3d:.2f}")
print()

# ============================================================================
# CAPACITY SCALING: GEOMETRY SWEEP
# ============================================================================
L_sweep = np.logspace(np.log10(10e-9), np.log10(100e-9), 10)
capacity_1d_sweep = []
capacity_2d_sweep = []
capacity_3d_sweep = []

print(f"Computing capacity scaling over L = 10nm to 100nm...")

for L_val in L_sweep:
    # Information capacity scaling (proportional to domain size relative to Debye length)
    debye_ratio = L_val / lambda_D

    # Theoretical capacity scaling
    C_1d = debye_ratio
    C_2d = debye_ratio**2
    C_3d = debye_ratio**3

    capacity_1d_sweep.append(C_1d)
    capacity_2d_sweep.append(C_2d)
    capacity_3d_sweep.append(C_3d)

capacity_1d_sweep = np.array(capacity_1d_sweep)
capacity_2d_sweep = np.array(capacity_2d_sweep)
capacity_3d_sweep = np.array(capacity_3d_sweep)

print(f"Capacity scaling computed.")
print()

# ============================================================================
# VISUALIZATION (Dark theme)
# ============================================================================
fig = plt.figure(figsize=(12, 9), dpi=150)
fig.patch.set_facecolor('#0d1117')

# Color scheme
bg_color = '#0d1117'
axes_color = '#161b22'
text_color = '#c9d1d9'

# Panel 1: 1D concentration profile
ax1 = plt.subplot(2, 2, 1)
ax1.set_facecolor(axes_color)
ax1.plot(x_1d*1e9, c_1d, color='#79c0ff', linewidth=2, label='1D Slab')
ax1.set_xlabel('Position (nm)', color=text_color, fontsize=11)
ax1.set_ylabel('Concentration (mol/m³)', color=text_color, fontsize=11)
ax1.set_title('Panel 1: 1D Slab Final Profile', color=text_color, fontsize=12, fontweight='bold')
ax1.tick_params(colors=text_color)
ax1.grid(True, alpha=0.2, color=text_color)
ax1.legend(facecolor=axes_color, edgecolor=text_color, labelcolor=text_color)

# Panel 2: 2D disk heatmap
ax2 = plt.subplot(2, 2, 2)
ax2.set_facecolor(axes_color)
# Heatmap in Cartesian coordinates with disk domain
pcm = ax2.pcolormesh(x_2d*1e9, y_2d*1e9, c_2d, shading='auto', cmap='viridis')
# Mask outside disk
ax2.contour(x_2d*1e9, y_2d*1e9, R_2d*1e9, levels=[L*1e9], colors='white', linewidths=1.5)
ax2.set_xlabel('X (nm)', color=text_color, fontsize=11)
ax2.set_ylabel('Y (nm)', color=text_color, fontsize=11)
ax2.set_title('Panel 2: 2D Disk Concentration', color=text_color, fontsize=12, fontweight='bold')
ax2.set_aspect('equal')
ax2.tick_params(colors=text_color)
cbar = plt.colorbar(pcm, ax=ax2)
cbar.set_label('Conc. (mol/m³)', color=text_color, fontsize=10)
cbar.ax.tick_params(colors=text_color)

# Panel 3: 3D sphere radial profile
ax3 = plt.subplot(2, 2, 3)
ax3.set_facecolor(axes_color)
ax3.plot(r_3d*1e9, c_3d, color='#7ee787', linewidth=2, label='3D Sphere')
ax3.set_xlabel('Radial Position (nm)', color=text_color, fontsize=11)
ax3.set_ylabel('Concentration (mol/m³)', color=text_color, fontsize=11)
ax3.set_title('Panel 3: 3D Sphere Radial Profile', color=text_color, fontsize=12, fontweight='bold')
ax3.tick_params(colors=text_color)
ax3.grid(True, alpha=0.2, color=text_color)
ax3.legend(facecolor=axes_color, edgecolor=text_color, labelcolor=text_color)

# Panel 4: Capacity scaling (log-log)
ax4 = plt.subplot(2, 2, 4)
ax4.set_facecolor(axes_color)
ax4.loglog(L_sweep*1e9, capacity_1d_sweep, 'o-', color='#1f77b4', linewidth=2,
          markersize=6, label='1D (∝ L)', alpha=0.8)
ax4.loglog(L_sweep*1e9, capacity_2d_sweep, 's-', color='#ff7f0e', linewidth=2,
          markersize=6, label='2D (∝ L²)', alpha=0.8)
ax4.loglog(L_sweep*1e9, capacity_3d_sweep, '^-', color='#2ca02c', linewidth=2,
          markersize=6, label='3D (∝ L³)', alpha=0.8)
ax4.set_xlabel('Domain Size (nm)', color=text_color, fontsize=11)
ax4.set_ylabel('Capacity (arb. units)', color=text_color, fontsize=11)
ax4.set_title('Panel 4: Information Capacity Scaling', color=text_color, fontsize=12, fontweight='bold')
ax4.tick_params(colors=text_color)
ax4.grid(True, alpha=0.2, color=text_color, which='both')
ax4.legend(facecolor=axes_color, edgecolor=text_color, labelcolor=text_color, loc='upper left')

# Apply text color to all tick labels
for ax in [ax1, ax2, ax3, ax4]:
    for spine in ax.spines.values():
        spine.set_color(text_color)
    for tick in ax.get_xticklabels() + ax.get_yticklabels():
        tick.set_color(text_color)

plt.tight_layout()

# Save figure
fig_path = '/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim13_3d_droplet.png'
plt.savefig(fig_path, facecolor=bg_color, edgecolor='none', bbox_inches='tight', dpi=150)
print(f"Figure saved to: {fig_path}")

plt.close()

# ============================================================================
# FINAL OUTPUT
# ============================================================================
print()
print("=" * 60)
print("SIMULATION 13: 3D SPHERICAL DROPLET GEOMETRY")
print("=" * 60)
print(f"1D entropy: {entropy_1d:.3f} bits")
print(f"2D entropy: {entropy_2d:.3f} bits")
print(f"3D entropy: {entropy_3d:.3f} bits")
print(f"2D/1D ratio: {ratio_2d:.3f}")
print(f"3D/1D ratio: {ratio_3d:.3f}")
print(f"3D/2D ratio: {ratio_3d/ratio_2d:.3f}")
print("=" * 60)
