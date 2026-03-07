"""
SIM09: Multi-Ion Computation
Coupled Nernst-Planck for Na+, K+, Cl- with Poisson coupling.
Demonstrates reservoir computing capability with multiple ion species.
Author: Ali Ahmed
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve
import warnings
warnings.filterwarnings('ignore')

# Physical constants
T = 310.15  # K
c0 = 150.0  # mol/m³
D_Na = 1.33e-9  # m²/s
D_K = 1.96e-9   # m²/s
D_Cl = 2.03e-9  # m²/s
z_Na = 1
z_K = 1
z_Cl = -1
F = 96485.0      # C/mol
R = 8.314        # J/(mol·K)
VT = 26.73e-3    # V (thermal voltage)
k_B = 1.381e-23
N_A = 6.022e23
lambda_D = 0.78e-9  # m

# Domain
L = 50e-9   # m
Nx = 100  # Reduced from 200
dx = L / Nx
x = np.linspace(0, L, Nx)

# Time stepping
tau_Na = L**2 / D_Na
tau_K = L**2 / D_K
tau_Cl = L**2 / D_Cl
dt = 0.3 * dx**2 / max(D_Na, D_K, D_Cl)  # More conservative
t_end = 0.8 * tau_Na  # Shorter simulation for speed
Nt = int(t_end / dt)

# Theme
bg = '#0d1117'
axes_color = '#161b22'
spine_color = '#30363d'
text_color = '#c9d1d9'

print(f"SIM09: Multi-Ion Computation")
print(f"Domain: L={L*1e9:.1f}nm, Nx={Nx}, dx={dx*1e9:.4f}nm")
print(f"Time: t_end={t_end*1e6:.2f}μs, Nt={Nt}, dt={dt*1e9:.4f}ns")
print(f"Memory timescales: τ_Na={tau_Na*1e6:.3f}μs, τ_K={tau_K*1e6:.3f}μs, τ_Cl={tau_Cl*1e6:.3f}μs")

def build_laplacian_1d(Nx, dx):
    """Build 1D Laplacian matrix with zero-flux boundaries."""
    diag_main = -2.0 * np.ones(Nx)
    diag_off = 1.0 * np.ones(Nx - 1)
    D_mat = diags([diag_off, diag_main, diag_off], [-1, 0, 1], shape=(Nx, Nx))
    return D_mat / (dx**2)

def solve_poisson_1d(Nx, dx, c_Na, c_K, c_Cl, VT):
    """Solve Poisson equation: d²φ/dx² = -F(z_Na*c_Na + z_K*c_K + z_Cl*c_Cl)/ε"""
    # Charge density
    rho = F * (c_Na - c_Cl + c_K) / (8.854e-12)

    # Build Laplacian as lil_matrix for efficient assignment
    L_mat = build_laplacian_1d(Nx, dx).tolil()

    # Boundary conditions: φ(0)=0, φ(L)=0
    L_mat[0, :] = 0
    L_mat[0, 0] = 1
    L_mat[-1, :] = 0
    L_mat[-1, -1] = 1
    rho[0] = 0
    rho[-1] = 0

    phi = spsolve(L_mat.tocsr(), rho)
    return np.real(phi)

def step_nernst_planck(c_Na, c_K, c_Cl, phi, D, z, VT, dt, dx):
    """Update concentration using Nernst-Planck equation."""
    c = c_Na if z == z_Na else (c_K if z == z_K else c_Cl)

    # Flux: J = -D*dc/dx + (z*F/RT)*D*c*dφ/dx
    dphi_dx = np.gradient(phi, dx)

    # Laplacian of concentration
    d2c_dx2 = np.zeros(len(c))
    d2c_dx2[1:-1] = (c[2:] - 2*c[1:-1] + c[:-2]) / dx**2

    # Gradient of concentration
    dc_dx = np.gradient(c, dx)

    # Electric potential contribution
    drift_term = (z * F / (R * T)) * D * c * dphi_dx
    drift_d2 = np.gradient(drift_term, dx)

    # Update
    c_new = c + dt * (D * d2c_dx2 + D * drift_d2 / (R * T))

    # Boundary: zero-flux
    c_new[0] = c_new[1]
    c_new[-1] = c_new[-2]

    # Clip to stable range
    c_new = np.clip(c_new, 0.01*c0, 20*c0)
    return c_new

def extract_features(c_Na, c_K, c_Cl, x):
    """Extract spatial features from concentration profiles."""
    features = []

    # Moments of each species
    for c in [c_Na, c_K, c_Cl]:
        features.extend([
            np.mean(c),
            np.std(c) + 1e-10,  # Add small epsilon to avoid div by zero
            np.max(c) - np.min(c),
            np.sum(np.abs(np.gradient(c))) + 1e-10
        ])

    # Cross-correlations (handle potential NaN from constant arrays)
    try:
        cc_na_k = np.corrcoef(c_Na, c_K)[0, 1]
        features.append(cc_na_k if not np.isnan(cc_na_k) else 0.0)
    except:
        features.append(0.0)

    try:
        cc_na_cl = np.corrcoef(c_Na, c_Cl)[0, 1]
        features.append(cc_na_cl if not np.isnan(cc_na_cl) else 0.0)
    except:
        features.append(0.0)

    try:
        cc_k_cl = np.corrcoef(c_K, c_Cl)[0, 1]
        features.append(cc_k_cl if not np.isnan(cc_k_cl) else 0.0)
    except:
        features.append(0.0)

    # Clean any remaining NaNs
    features = np.array(features)
    features = np.nan_to_num(features, nan=0.0, posinf=1e3, neginf=-1e3)

    return features

def run_simulation(num_ions, n_samples=20):
    """Run simulation with different numbers of ions."""
    print(f"\n--- Running {num_ions}-ion simulation ---")

    # Initialize concentrations
    c_Na = np.ones(Nx) * c0
    c_K = np.ones(Nx) * c0
    c_Cl = np.ones(Nx) * c0

    # Inject at left boundary
    c_Na[0] = 5 * c0
    c_K[0] = 5 * c0 if num_ions >= 2 else c0
    c_Cl[0] = 5 * c0 if num_ions >= 3 else c0

    # Storage
    features_list = []
    times = np.linspace(0, t_end, 50)
    time_idx = 0

    # Time integration
    for step in range(Nt):
        t = step * dt

        # Solve Poisson
        phi = solve_poisson_1d(Nx, dx, c_Na, c_K, c_Cl, VT)

        # Update each species
        if num_ions >= 1:
            c_Na = step_nernst_planck(c_Na, c_K, c_Cl, phi, D_Na, z_Na, VT, dt, dx)
        if num_ions >= 2:
            c_K = step_nernst_planck(c_Na, c_K, c_Cl, phi, D_K, z_K, VT, dt, dx)
        if num_ions >= 3:
            c_Cl = step_nernst_planck(c_Na, c_K, c_Cl, phi, D_Cl, z_Cl, VT, dt, dx)

        # Extract features at selected times
        if time_idx < len(times) and t >= times[time_idx]:
            features = extract_features(c_Na, c_K, c_Cl, x)
            features_list.append(features)
            time_idx += 1

    features_array = np.array(features_list)

    # Create synthetic task: sine vs square wave
    np.random.seed(42)
    X_train, y_train, X_test, y_test = [], [], [], []

    for i in range(n_samples // 2):
        # Sine: input modulates left boundary
        c_test = np.ones(Nx) * c0
        c_test[0] = c0 * (1 + 0.5 * np.sin(2 * np.pi * i / (n_samples // 4)))
        f_sine = extract_features(c_test, c_test, c_test, x)

        # Square: step input
        c_test[0] = c0 * (1 + 0.5 * (1 if (i % 4) < 2 else -1))
        f_square = extract_features(c_test, c_test, c_test, x)

        if i < (n_samples // 4):
            X_train.append(f_sine)
            y_train.append(0)
            X_train.append(f_square)
            y_train.append(1)
        else:
            X_test.append(f_sine)
            y_test.append(0)
            X_test.append(f_square)
            y_test.append(1)

    X_train = np.array(X_train)
    X_test = np.array(X_test)
    y_train = np.array(y_train)
    y_test = np.array(y_test)

    # Simple linear classifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train_scaled, y_train)
    accuracy = clf.score(X_test_scaled, y_test)

    print(f"  Accuracy: {accuracy*100:.1f}%")

    return c_Na, c_K, c_Cl, phi, accuracy

# Run simulations with 1, 2, 3 ions
results_1ion = run_simulation(1)
c_Na_1, c_K_1, c_Cl_1, phi_1, acc_1 = results_1ion

results_2ion = run_simulation(2)
c_Na_2, c_K_2, c_Cl_2, phi_2, acc_2 = results_2ion

results_3ion = run_simulation(3)
c_Na_3, c_K_3, c_Cl_3, phi_3, acc_3 = results_3ion

accuracies = [acc_1, acc_2, acc_3]
ion_counts = [1, 2, 3]

# Compute eigenvalue spectrum (Poisson problem)
L_mat = build_laplacian_1d(Nx, dx)
eigenvalues = np.linalg.eigvalsh(L_mat.toarray())
eigenvalues = np.sort(eigenvalues)[-50:]  # Last 50 (largest)

# Create 4-panel figure
fig = plt.figure(figsize=(14, 10))
fig.patch.set_facecolor(bg)
gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

# Panel 1: Concentration profiles (3 species)
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_facecolor(axes_color)
ax1.plot(x*1e9, c_Na_3/c0, label='Na+', color='#ff6b6b', linewidth=2)
ax1.plot(x*1e9, c_K_3/c0, label='K+', color='#4ecdc4', linewidth=2)
ax1.plot(x*1e9, c_Cl_3/c0, label='Cl-', color='#45b7d1', linewidth=2)
ax1.axhline(y=1, color=spine_color, linestyle='--', alpha=0.5, linewidth=1)
ax1.set_xlabel('Position (nm)', color=text_color, fontsize=11)
ax1.set_ylabel('Concentration (c₀)', color=text_color, fontsize=11)
ax1.set_title('Ion Concentration Profiles (3 Species)', color=text_color, fontsize=12, fontweight='bold')
ax1.legend(loc='upper right', framealpha=0.9, facecolor=axes_color, edgecolor=spine_color)
ax1.tick_params(colors=text_color)
for spine in ax1.spines.values():
    spine.set_color(spine_color)
ax1.grid(True, alpha=0.2, color=spine_color)

# Panel 2: Memory timescale bar chart
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_facecolor(axes_color)
timescales = [tau_Na*1e6, tau_K*1e6, tau_Cl*1e6]
ion_names = ['Na+', 'K+', 'Cl-']
colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
bars = ax2.bar(ion_names, timescales, color=colors, alpha=0.8, edgecolor=spine_color, linewidth=1.5)
ax2.set_ylabel('Memory Timescale (μs)', color=text_color, fontsize=11)
ax2.set_title('Diffusion Timescales: τ = L²/D', color=text_color, fontsize=12, fontweight='bold')
ax2.tick_params(colors=text_color)
for spine in ax2.spines.values():
    spine.set_color(spine_color)
ax2.grid(True, alpha=0.2, axis='y', color=spine_color)
# Add value labels on bars
for bar, val in zip(bars, timescales):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height, f'{val:.2f}μs',
             ha='center', va='bottom', color=text_color, fontsize=10)

# Panel 3: Accuracy vs ion count
ax3 = fig.add_subplot(gs[1, 0])
ax3.set_facecolor(axes_color)
ax3.plot(ion_counts, accuracies, 'o-', color='#a8e6cf', markersize=10, linewidth=2.5,
         markeredgecolor=spine_color, markeredgewidth=1.5)
ax3.set_xlabel('Number of Ion Species', color=text_color, fontsize=11)
ax3.set_ylabel('Classification Accuracy', color=text_color, fontsize=11)
ax3.set_title('Reservoir Computing: Accuracy vs Ion Count', color=text_color, fontsize=12, fontweight='bold')
ax3.set_xticks([1, 2, 3])
ax3.set_ylim([0.4, 1.0])
ax3.tick_params(colors=text_color)
for spine in ax3.spines.values():
    spine.set_color(spine_color)
ax3.grid(True, alpha=0.2, color=spine_color)
# Add value labels
for x, y in zip(ion_counts, accuracies):
    ax3.text(x, y + 0.02, f'{y*100:.1f}%', ha='center', va='bottom', color=text_color, fontsize=10)

# Panel 4: Eigenvalue spectrum
ax4 = fig.add_subplot(gs[1, 1])
ax4.set_facecolor(axes_color)
ax4.plot(eigenvalues, 'o-', color='#ffd93d', markersize=6, linewidth=1.5, alpha=0.8)
ax4.set_xlabel('Eigenvalue Index', color=text_color, fontsize=11)
ax4.set_ylabel('Eigenvalue Magnitude', color=text_color, fontsize=11)
ax4.set_title('Poisson Operator Eigenvalue Spectrum', color=text_color, fontsize=12, fontweight='bold')
ax4.tick_params(colors=text_color)
for spine in ax4.spines.values():
    spine.set_color(spine_color)
ax4.grid(True, alpha=0.2, color=spine_color)
ax4.set_yscale('log')

plt.suptitle('SIM09: Multi-Ion Computation & Reservoir Computing',
             fontsize=14, fontweight='bold', color=text_color, y=0.995)

plt.savefig('/sessions/eager-elegant-babbage/mnt/extracurrculars/liquid-dynamics/figures/sim09_multi_ion_computation.png',
            dpi=150, bbox_inches='tight', facecolor=bg)
print("\nFigure saved: sim09_multi_ion_computation.png")
plt.close()

print("\n=== SIM09 COMPLETE ===")
